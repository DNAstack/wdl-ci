class HydrateParams(object):
    @classmethod
    def hydrate(cls, source, target, workflow_name=""):
        result = {}
        separator = "" if workflow_name == "" else "."

        for tk in target.keys():
            tv = target[tk]

            for sk in source.keys():
                sv = source[sk]
                tv = tv.replace("${" + sk + "}", sv)

            result[f"{workflow_name}{separator}{tk}"] = tv
        return result
