# ============================================================
# Add new website by copying 1 block below and editing it
# category options: "news", "shopping", "books", "other"
# ============================================================

vnexpress = {
    "name"           : "VnExpress",
    "base_url"       : "https://vnexpress.net",
    "index_url"      : "https://vnexpress.net/tin-tuc-24h",
    "category"       : "news",
    "link_selector"  : "h3.title-news a",
    "title_selector" : "h1.title-detail",
    "fields"         : {
        "author"  : "strong.author",
        "content" : "article.fck_detail"
    }
}

# tuoitre = {
#     "name"           : "Tuoi Tre",
#     "base_url"       : "https://tuoitre.vn",
#     "index_url"      : "https://tuoitre.vn/tin-moi-nhat.htm",
#     "category"       : "news",
#     "link_selector"  : "a.box-category-item",
#     "title_selector" : "h1.article-title",
#     "fields"         : {
#         "author"  : "span.author-name",
#         "content" : "div.detail-content"
#     }
# }

fahasa = {
    "name"           : "Fahasa",
    "base_url"       : "https://www.fahasa.com",
    "index_url"      : "https://www.fahasa.com/sach-trong-nuoc.html",
    "category"       : "books",
    "link_selector"  : "a.product-item-link",
    "title_selector" : "h1.page-title",
    "fields"         : {
        "price"  : "span.price",
        "author" : "div.product-attribute-author"
    }
}

# shopee = {
#     "name"           : "Shopee",
#     "base_url"       : "https://shopee.vn",
#     "index_url"      : "https://shopee.vn/Thoi-Trang-Nam-cat.11035567",
#     "category"       : "shopping",
#     "link_selector"  : "a.shopee-item",
#     "title_selector" : "div.product-name",
#     "fields"         : {
#         "price" : "div.product-price"
#     }
# }

# ============================================================
# Add all active sites to this list
# To disable a site: remove it from the list below
# ============================================================
ALL_SITES = [
    vnexpress,
    # tuoitre,
    fahasa,
    # shopee,
]