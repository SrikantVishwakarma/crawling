import scrapy
import re
from w3lib.html import remove_tags

class ProtoSpider(scrapy.Spider):
    name = 'proto'
    start_urls = [
        'https://www.protoindustrial.com/en/industrial-tools/BrandPage/Proto/',
        'https://www.protoindustrial.com/en/industrial-tools/BrandPage/StanleyTools/'
    ]

    def parse(self, response):
        cat_urls = response.css('div.mod-facets.is-semi-expanded a::attr(href)').getall()
        cat_names = response.css('div.mod-facets.is-semi-expanded a span::text').getall()
        i = 0
        # print(cat_names)
        for cat_url in cat_urls:
            cat_url = response.urljoin(cat_url) + 'page-1/display-100/'
            cat_name = cat_names[i]
            i += 1
            # if "Tethered Tool" not in cat_name:
            #     continue
            yield scrapy.Request(url=cat_url, callback=self.parse_cat, dont_filter=True, meta={"Category": cat_name})

           
    def parse_cat(self, response):
        cat_name = response.meta['Category']
        try:
            sub_con = re.search(r'class="_f-title">Sub-Category</h3>(.*?)</div>', str(response.body)).group(1)
            subcat_urls =  re.findall(r'href="(.*?)"', str(sub_con), flags=re.M|re.S)
            subcat_names = re.findall(r'id=.*?><span>(.*?)<', str(sub_con), flags=re.M|re.S)
        except:
            subcat_urls = []
            subcat_names = []

        if len(subcat_urls) != 0:
            i = 0
            for subcat_url in subcat_urls:
                subcat_url = response.urljoin(subcat_url) + 'display-100/'
                subcat_name = subcat_names[i]
                i += 1
                # if 'Tether-Ready Hand Sockets' not in subcat_name:
                #     continue 
                yield scrapy.Request(
                    url=subcat_url,
                    callback=self.parse_subcat,
                    dont_filter=True,
                    meta={"Category": cat_name, "Subcategory": subcat_name}
                )
        else:           
            prod_url_sel = response.css('section.mod-product-result-item')
            for url_sel in prod_url_sel:
                prod_id =  url_sel.css("[class='_pri-id'] span::text").get()
                if prod_id is not None:
                    prod_url = url_sel.css('[class="_pri-description"] a::attr(href)').get().strip()
                    prod_url = response.urljoin(prod_url)
                    # print(f"PROD URL without SUB =={prod_id}==", prod_url)
                    yield scrapy.Request(
                        url=prod_url, callback=self.parse_prodpage, dont_filter=True,
                        meta={"Category": cat_name, "Subcategory": None}
                    )
                else:
                    detail_url = url_sel.css('[class="_pri-description"] a::attr(href)').get()
                    detail_url = response.urljoin(detail_url)
                    # print("PROD DETAIL URL====", detail_url)
                    yield scrapy.Request(
                        url=detail_url,
                        callback=self.parse_detail,
                        dont_filter=True,
                        meta={"Category": cat_name, "Subcategory": None}
                    )
            # pagination
            next_page = response.css('[class="_p-page-numbers"] a::attr(href)').get()
            if next_page is not None:
                next_page = response.urljoin(next_page)
                print("NEXT Page Without SUB========", next_page)
                yield response.follow(next_page, callback=self.parse_prodpage)
            
    def parse_subcat(self, response):
        cat_name = response.meta["Category"]
        sub_cat = response.meta["Subcategory"]
        prod_url_sel = response.css('section.mod-product-result-item')
        for url_sel in prod_url_sel:
            prod_id =  url_sel.css("[class='_pri-id'] span::text").get()
            if prod_id is not None:
                prod_url = url_sel.css('[class="_pri-description"] a::attr(href)').get().strip()
                prod_url = response.urljoin(prod_url)
                yield scrapy.Request(url=prod_url, callback=self.parse_prodpage, dont_filter=True,
                meta={"Category": cat_name, "Subcategory": sub_cat}
                )
            else:
                detail_url = url_sel.css('[class="_pri-description"] a::attr(href)').get()
                detail_url = response.urljoin(detail_url)
                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail,
                    dont_filter=True,
                    meta={"Category": cat_name, "Subcategory": sub_cat}
                )
        # pagination
        next_page = response.css('[class="_p-page-numbers"] a::attr(href)').get()
        if next_page is not None:
            next_page = response.urljoin(next_page)
            print("NEXT Page SUB========", next_page)
            yield response.follow(next_page, callback=self.parse_subcat)

     
    def parse_detail(self, response):
        cat_name = response.meta["Category"]
        sub_cat = response.meta["Subcategory"]
        prod_urls = response.css('div.mod-sku-list a::attr(href)').getall()
        prod_urls = [url for url in prod_urls if '_layouts' not in url]
        # print(f"PRODDUCT  URL+++++++++++++: {response.url} ===={prod_urls}====")
        
        for prod_url in prod_urls:
            prod_url = response.urljoin(prod_url)
            # print("PARSE DETAIL prod URL ==== ", prod_url)
            yield scrapy.Request(
                url=prod_url,
                callback=self.parse_prodpage,
                dont_filter=True,
                meta={"Category": cat_name, "Subcategory": sub_cat}
            )

    def parse_prodpage(self, response):
        cat_name = response.meta["Category"]
        cat_name = re.sub(r'\s*\(\w+\)\s*', '', cat_name)
        sub_cat = response.meta["Subcategory"]
        if sub_cat is not None:
            sub_cat = re.sub(r'\s*\(\w+\)\s*', '', str(sub_cat))
        
        spec_sel = response.css('[class="mod-product-tabs-content mod-rtf-light is-visuallyhidden mod-product-spec hlp-print"]')
        head = spec_sel.css('th::text').getall()
        value = spec_sel.css('td::text').getall()
        head = [remove_tags(h).strip() for h in head]
        value = [remove_tags(v).strip() for v in value]
        
        spec = dict(zip(head, value))
        if len(spec.keys()) is 0:
            spec = None

        feature_bene = response.css('[class="mod-product-tabs-content mod-rtf-light"] li::text').getall()
        feature_bene = "|".join(feature_bene)
        prod_name = response.css('[class="_pd-name"]::text').get().strip()
        pid = response.css('[id="ctl00_PlaceHolderMain_ctl00_SkuDisplayerControl_ProductProtoSkuLabel"]::text').get().strip()
        brand = 'Stanley' if 'StanleyTools' in response.url else 'Proto'
        # image
        d_img = response.css('[class="_pi-thumbnails hlp-line-align hlp-no-print"] a::attr(href)').getall()
        d_img = [d for d in d_img if 'youtube' not in d]
        i_img = response.css('[class="_pi-thumbnails hlp-line-align hlp-no-print"] img::attr(src)').getall()
        i_img = [i for i in i_img if 'youtube' not in i]
        z_img = response.css('[class="_pi-thumbnails hlp-line-align hlp-no-print"] a::attr(data-hight-res)').getall()
        z_img = [z for z in z_img if 'youtube' not in z]

        yt_url = [z for z in z_img if 'youtube' in z]

        image_list = list()
        for img in zip(i_img, d_img, z_img):
            temp_img = dict()
            temp_img['Item_Image'] = img[0]
            temp_img['Detailed_Image'] = img[1]
            temp_img['Zoom_Image'] = img[2]
            image_list.append(temp_img)


        result = dict()
        result["URL"] = response.url
        result["Category"] = cat_name
        result["Subcategory"] = sub_cat
        result['Prod_Name'] = prod_name
        result['Prod_ID'] = pid
        result['Brand'] = brand
        result["Specifications"] = spec
        result['Videos'] = yt_url
        result["FeaturesAndBenefits"] = feature_bene
        result['Images'] = image_list
        
        yield result
    
        
    