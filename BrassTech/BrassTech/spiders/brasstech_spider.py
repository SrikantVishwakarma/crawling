import scrapy
import os
import re
from w3lib.html import remove_tags


class BrassTechSpider(scrapy.Spider):
    name = "BrassTech"
    start_urls = ['https://www.newportbrass.com/products/categories/','https://www.gingerco.com/products/categories/']
   
    def parse(self, response):
        url_con = response.css('[class="col-sm-4 col-md-3"]')[0]
        cat_urls  = url_con.css('a::attr(href)').getall()
        cat_urls = cat_urls[1:-1]
        cat_names = url_con.css('a::text').getall()
        cat_names = cat_names[1:-1]
        i = 0
        for cat_url in cat_urls:
            cat_url = response.urljoin(cat_url)
            cat_name = cat_names[i]
            i += 1
            yield scrapy.Request(
                url=cat_url,
                callback=self.parse_cat,
                dont_filter=True,
                meta={"Category":cat_name}
            )
    
    def parse_cat(self, response):
        cat_name = response.meta["Category"]
        sub_cat_urls = response.css('[class="col-xxs-6 col-xs-4 col-md-3"] ::attr(href)').extract()
        sub_cat_names = [url.split("/")[-2] for url in sub_cat_urls]
        i = 0
        for sub_cat_url in sub_cat_urls:
            sub_cat_name = sub_cat_names[i]
            sub_cat_url = response.urljoin(sub_cat_url)
            i += 1
            yield scrapy.Request(
                url=sub_cat_url,
                callback=self.parse_subcat,
                dont_filter=True,
                meta={"Category": cat_name, "Subcategory": sub_cat_name},
            )

    def parse_subcat(self, response):
        cat_name = response.meta["Category"].title()
        sub_cat_name = response.meta["Subcategory"].title()

        prod_urls = response.css('[class="col-xxs-6 col-xs-4 col-md-3"] ::attr(href)').extract()

        for prod_url in prod_urls:
            prod_url = response.urljoin(prod_url)
            yield scrapy.Request(
                url=prod_url, callback=self.parse_prodpage, dont_filter=True, 
                meta={"Category":cat_name, "Subcategory":sub_cat_name})

    def parse_prodpage(self, response):
        cat_name = response.meta["Category"].title()
        sub_cat_name = response.meta["Subcategory"].title()
        short_des = response.css('[id="productDetails"] li::text').getall()
        short_des = [sd.strip() for sd in short_des]
        short_des = "|".join(short_des)
        price = response.css('[id="productDetails"] dd::text')[1].get().strip()
        current_finish = response.css('[id="productDetails"] dd::text').get().strip()
        b_crumb =  response.css('[class="breadcrumb"] a::text').getall()
        prod_id = b_crumb[-1].strip()
        b_crumb = "/".join(b_crumb)
        series = response.css('[id="pageHeaderControl_btBreadCrumbs_lblSectionName"] ::text').get()
        prod_name = response.css('[id="productDetails"] p::text').get().strip()
        title = response.css('title::text').get()
        title = re.sub(r'\r\n|\t','', title)

        brand = response.css('[class="list-inline"] a::text').re(r'About (.*)')[0]
        prod_details = response.css('[id="tab2_ProductDetailsTab"] li::text').getall()
        prod_details = [pd.strip() for pd in prod_details]
        prod_details = "|".join(prod_details)
        # pdf docs
        doc_names = response.css('[id="TILGeneral"] a::text').getall()
        doc_urls = response.css('[id="TILGeneral"] a::attr(href)').getall()
        doc_urls = [response.urljoin(doc_url) for doc_url in doc_urls if '.pdf' in doc_url]
        doc_names = doc_names[:len(doc_urls)]
        docs =  dict(zip(doc_names, doc_urls)) if len(doc_urls) > 0 else None

        # drawing docs
        dwg_2d_names = response.css('[id="TIL2D"] a::text').getall()
        dwg_2d_urls = response.css('[id="TIL2D"] a::attr(href)').getall()
        dwg_2d_urls = [response.urljoin(u) for u in dwg_2d_urls]

        dwg_3d_names = response.css('[id="TIL3D"] a::text').getall()
        dwg_3d_urls = response.css('[id="TIL3D"] a::attr(href)').getall()
        dwg_3d_urls = [response.urljoin(u) for u in dwg_3d_urls]
        
        dwg_2d_names.extend(dwg_3d_names)
        dwg_2d_urls.extend(dwg_3d_urls)

        dwg_docs = dict(zip(dwg_2d_names, dwg_2d_urls)) if len(dwg_2d_urls) > 0 else None        
        # images
        zoom_img = response.css('[class="altLinks"] a::attr(href)').getall()
        zoom_img = [response.urljoin(img_url) for img_url in zoom_img if('#' not in img_url)]
        if len(zoom_img) == 0:
            m_obj = re.search(r'id="hProductZoomUrl"\s*value="(.*?)"', str(response.body), re.I|re.M)
            if m_obj:
                xml_file = m_obj.group(1)
                img_url = xml_file.replace('_NF.xml', '_NF_files/8/0_0.jpg')
                img_url = response.urljoin(img_url)
                zoom_img.append(img_url)

        alt_img_en = response.css('[class="alternate-images"] a::attr(href)').getall()
        alt_img_en = [response.urljoin(alt_img) for alt_img in alt_img_en]

        images_list = list()
        for img_list in [zoom_img, alt_img_en]:
            for img_url in img_list: 
                img_dict = dict()
                img_dict['Item_Image'] = img_url
                img_dict['Detailed_Image'] = img_url
                img_dict['Zoom_Image'] = img_url
                images_list.append(img_dict)

        meta_desc = re.search(r'name="description"\s*content="(.*?)"', str(response.body)).group(1)
        meta_key = re.search(r'name="keywords"\s*content="(.*?)"', str(response.body)).group(1)
        
        print(meta_key , meta_key)

        yield {
            "Url": response.url,
            "Breadcrumb": b_crumb,
            "Title": title,
            "Product_Name": prod_name,
            "Series": series,
            "Brand_Name": brand,
            "Category": cat_name,
            "Subcategory": sub_cat_name,
            "Product_ID": prod_id,
            "Price": price,
            "Finish": current_finish,
            "Short_Description": short_des,
            "Description": prod_details,
            "Meta_Description": meta_desc,
            "Meta_Key": meta_key,
            "Documents": docs,
            "Drawing_Docs": dwg_docs,
            "Images": images_list     
        }
