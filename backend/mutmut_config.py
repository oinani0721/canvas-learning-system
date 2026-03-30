def pre_mutation(context):
    if "test" in context.filename:
        context.skip = True
