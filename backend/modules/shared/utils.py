
def paginate(items, page: int = 1, page_size: int = 20):
    start = (page - 1) * page_size
    end = start + page_size
    return items[start:end]
