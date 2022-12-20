class HydrateParams(object):

    @classmethod
    def hydrate(cls, source, target):
        result = {}

        for tk in target.keys():
            tv = target[tk]

            for sk in source.keys():
                sv = source[sk]
                tv = tv.replace("${" + sk + "}", sv)
            
            result[tk] = tv
        return result
