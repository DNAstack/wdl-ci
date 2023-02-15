class HydrateParams(object):
    @classmethod
    def hydrate(cls, source, target, update_key=True, workflow_name=""):
        result = {}
        separator = "" if workflow_name == "" else "."

        for tk in target.keys():
            tv = target[tk]
            if type(tv) is str:
                for sk in source.keys():
                    sv = source[sk]
                    tv = tv.replace("${" + sk + "}", sv)

            new_key = f"{workflow_name}{separator}{tk}" if update_key else tk
            result[new_key] = tv
        return result
