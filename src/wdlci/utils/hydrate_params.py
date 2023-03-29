import re

variable_regex = re.compile("\${[^}]+}")


class HydrateParams(object):
    @classmethod
    def hydrate(cls, source, target, update_key=True, workflow_name=""):
        result = {}
        separator = "" if workflow_name == "" else "."

        def _replace_value_recursive(target_value):
            if type(target_value) is str and variable_regex.search(target_value):
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
                                source_value
                            )
                            target_value = source_value_substituted
                        # If the source key is found in the target_value but is not the only contents of target_value, emit an error
                        elif type(target_value) is str and re.search(
                            rf"\${{{source_key}}}", target_value
                        ):
                            raise SystemExit(
                                f'[ERROR] Cannot set complex parameter {source_key} for target key [{target_key}]; in order to set a non-string parameter (e.g. dict or array) to a value it must be the sole content of the target\nAllowed:\n\t"{target_key}": "${{{source_key}}}"\nYou had:\n\t"{target_key}": "{target_value}"'
                            )
                return _replace_value_recursive(target_value)
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
                return substituted_dict
            elif type(target_value) is int or type(target_value) is bool:
                return target_value
            else:
                raise SystemExit(
                    f"Unexpected type [{type(target_value)}] detected for value {target_value}"
                )

        for target_key, target_value in target.items():
            target_value_substituted = _replace_value_recursive(target_value)

            new_key = (
                f"{workflow_name}{separator}{target_key}" if update_key else target_key
            )
            result[new_key] = target_value_substituted
        return result
