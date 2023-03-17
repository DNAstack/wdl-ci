class HydrateParams(object):
    @classmethod
    def hydrate(cls, source, target, update_key=True, workflow_name=""):
        result = {}
        separator = "" if workflow_name == "" else "."

        def _replace_value_recursive(target_value):
            if type(target_value) is str:
                for sk in source.keys():
                    sv = source[sk]
                    target_value = target_value.replace("${" + sk + "}", sv)
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
            else:
                raise SystemExit(f"Unexpected type detected for value {target_value}")

        for tk in target.keys():
            tv = target[tk]
            tv = _replace_value_recursive(tv)

            new_key = f"{workflow_name}{separator}{tk}" if update_key else tk
            result[new_key] = tv
        return result
