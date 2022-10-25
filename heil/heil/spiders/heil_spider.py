import scrapy
import re
from w3lib.html import remove_tags


class HeilSpider(scrapy.Spider):
    name = 'heil'
    start_urls = ['https://www.heil-hvac.com/en/us/']

    def parse(self, response):
        url_sel = response.css('[class="dropdown-item"]')[0]
        cat_urls = url_sel.css('a::attr(href)').getall()[:-1]
        cat_names = url_sel.css('a::text').getall()[:-1]
        cat_names = [cn.replace('\n', '') for cn in cat_names]
        i = 0
        for cat_url in cat_urls:
            cat_url = response.urljoin(cat_url)
            cat_name = cat_names[i]
            i += 1
            yield scrapy.Request(url=cat_url, callback=self.parse_cat, dont_filter=True, meta={"Category": cat_name})
            
    def parse_cat(self, response):
        cat_name = response.meta['Category']
        series_ids = response.css('[id="show"] option::attr(value)').getall()
        series_names = response.css('[id="show"] option::text').getall()
        series_map = dict(zip(series_ids, series_names))
        for series_sel in response.css('[class="product-list"]'):
            s_id = series_sel.css('div.product-list::attr(id)').get()
            prod_urls = series_sel.css('[class="card-subtitle"] a::attr(href)').getall()
            data = {}
            data['Category'] = cat_name
            data['Series'] = series_map.get(s_id, None)
            for prod_url in prod_urls:
                prod_url = response.urljoin(prod_url)
                yield scrapy.Request(url=prod_url, callback=self.parse_prod, dont_filter=True, meta=data)

    def parse_prod(self, response):
        cat_name = response.meta['Category']
        series = response.meta['Series']
        des_sel = response.css('[class="product-description card-text"]')
        prod_id = des_sel.css('[class="h2"]::text').get().strip()
        prod_name = des_sel.css('[class="h3"]::text').get().strip()
        m_ob = re.search(r'<p>(.*?)</p>', str(des_sel.get()), re.M|re.DOTALL)
        sort_desc = m_ob.group(1) if m_ob else ''
        sort_desc = remove_tags(sort_desc).strip()
        sort_desc = sort_desc.replace('\n', '') 
        # sort_desc = des_sel.css('p::text').get().strip()
        
        if sort_desc == '' or sort_desc is None:
            sort_desc = des_sel.css('p+p::text').get()
            sort_desc = sort_desc.strip() if sort_desc else sort_desc
            if sort_desc == '' or sort_desc is None:
                sort_desc = des_sel.css('p+div+div::text').get()

           
        long_des_sel = response.css('[class="col-md-7 product-detail-list-items"]')
        long_des_headers = long_des_sel.css('[class="text-detail"] h5::text').getall()
        long_desc = long_des_sel.css('[class="text-detail"] p::text').getall()
        long_desc_dict = dict(zip(long_des_headers, long_desc))
        if not long_desc_dict:
            long_desc_dict = None 

        
        result = dict()
        result['URL'] =  response.url
        result['Category'] = cat_name
        result['Series'] = series
        result['Prod_Name'] = prod_name
        result['Prod_ID'] = prod_id
        result['Short_Description'] =  sort_desc
        result['Long_Description'] = long_desc_dict

        spec_sel = response.css('[class="card"]')

        for s in spec_sel:
            spec_header = s.css('span::text').get()
            if 'Product' in spec_header:
                # p_sel = s.css('[class="product-detail-spec"]')
                # pspec_key =  s.css('span::text').getall()
                pspec_key = re.findall(r'<span>(.*?)</span>', str(s.get()))
                pspec_key = [remove_tags(k) for k in pspec_key if '\n' not in k][1:]
                pspec_value = s.css('[class="product-detail-spec-value"]::text').getall()
                pspec_value = [k.strip() for k in pspec_value]
                p_details = dict(zip(pspec_key, pspec_value))
                result[spec_header] = p_details
            else:
                spec_values = s.css('li::text').getall()
                spec_values = '|'.join(spec_values)
                result[spec_header] = spec_values


        yield result