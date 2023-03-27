class HydrateParams(object):
    @classmethod
    def hydrate(cls, source, target, update_key=True, workflow_name=""):
        result = {}
        separator = "" if workflow_name == "" else "."

        def _replace_value_recursive(target_value):
            if type(target_value) is str:
                for source_key, source_value in source.items():
                    target_value = target_value.replace(
                        "${" + source_key + "}", source_value
                    )
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
