import re
import copy
from wdlci.exception.wdl_test_cli_exit_exception import WdlTestCliExitException

variable_regex = re.compile("\${[^}]+}")
# The entire target value is enclosed in a variable
#   ${reference.reference_fasta}
subvariable_regex = re.compile("^\${[^{}\$]+\.[^{}\$]+}$")
# The target value is comprised of variable and non-variable segments: not supported
#   gs://my_bucket/${reference.reference_fasta}
subvariable_regex_nonvar = re.compile("\${[^{}\$]+\.[^{}\$]+}")


class HydrateParams(object):
    @classmethod
    def hydrate(cls, source, target, update_key=True, workflow_name=""):
        result = {}
        separator = "" if workflow_name == "" else "."

        def _replace_value_recursive(target_value, subkeys=[]):
            if type(target_value) is str and variable_regex.search(target_value):
                # Referring to struct members, e.g. reference.reference_fasta
                if subvariable_regex.search(target_value):
                    object_selector = target_value.lstrip("${").rstrip("}").split(".")
                    target_value = "${" + object_selector[0] + "}"
                    subkeys = object_selector[1:]
                elif subvariable_regex_nonvar.search(target_value):
                    raise WdlTestCliExitException(
                        f'Selecting struct members when this selector is not the only item present in the target value is not currently supported.\nTry again using only:\n\t"${{key.subkey[.subkey]}}"\nYou had:\n\t"{target_value}"',
                        1,
                    )
                for source_key, source_value in source.items():
                    # Don't try replacing the source value when it's non-string
                    # Need to keep checking that target_value is still str because it could be replaced with a complex object
                    if type(target_value) is str and type(source_value) is str:
                        target_value = target_value.replace(
                            "${" + source_key + "}", source_value
                        )
                    else:
                        # If the target value selects only a source_key whose type is non-string
                        # Return the substituted version of that source_value
                        # Only matches if the source_key is the _only_ contents of target_value; otherwise emit an error
                        if type(target_value) is str and re.match(
                            rf"^\${{{source_key}}}$", target_value
                        ):
                            source_value_substituted = _replace_value_recursive(
                                source_value, subkeys
                            )
                            target_value = source_value_substituted
                        # If the source key is found in the target_value but is not the only contents of target_value, emit an error
                        elif type(target_value) is str and re.search(
                            rf"\${{{source_key}}}", target_value
                        ):
                            raise WdlTestCliExitException(
                                f'[ERROR] Cannot set complex parameter {source_key} for target key [{target_key}]; in order to set a non-string parameter (e.g. dict or array) to a value it must be the sole content of the target\nAllowed:\n\t"{target_key}": "${{{source_key}}}"\nYou had:\n\t"{target_key}": "{target_value}"',
                                1,
                            )
                return _replace_value_recursive(target_value, subkeys)
            # If the target_value is type string and no longer has any variables to substitute
            elif type(target_value) is str:
                return target_value
            elif type(target_value) is list:
                substituted_list = list()
                for item in target_value:
                    substituted_list.append(_replace_value_recursive(item))
                return substituted_list
            elif type(target_value) is dict:
                substituted_dict = dict()
                for key, value in target_value.items():
                    substituted_dict[key] = _replace_value_recursive(value)
                if len(subkeys) > 0:
                    substituted_value = copy.deepcopy(substituted_dict)
                    for subkey in subkeys:
                        if type(substituted_value) is not dict:
                            raise WdlTestCliExitException(
                                f"Cannot select key '{subkey}' from non-dict '{substituted_value}'; check your data structure?\nInitial dict being traversed:\n{substituted_dict}",
                                1,
                            )
                        try:
                            substituted_value = substituted_value[subkey]
                        except KeyError:
                            raise WdlTestCliExitException(
                                f"Key '{subkey}' not found in {substituted_value.keys()}.\nInitial dict being traversed:\n{substituted_dict}",
                                1,
                            )
                    return substituted_value
                else:
                    return substituted_dict
            elif (
                type(target_value) is int
                or type(target_value) is bool
                or type(target_value) is float
            ):
                return target_value
            else:
                raise WdlTestCliExitException(
                    f"Unexpected type [{type(target_value)}] detected for value {target_value}",
                    1,
                )

        for target_key, target_value in target.items():
            target_value_substituted = _replace_value_recursive(target_value)

            new_key = (
                f"{workflow_name}{separator}{target_key}" if update_key else target_key
            )
            result[new_key] = target_value_substituted

        return result
