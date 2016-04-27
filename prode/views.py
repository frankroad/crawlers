import requests
from pyquery import PyQuery as pq
from rest_framework.views import APIView
from rest_framework.response import Response
from prode.models import Goods
from flash import constant


class GoodsList(APIView):

    def get_url(self, keywords, page, source):
        amazon_url = constant.AMAZON_URL.format(page=page, keywords=keywords)
        data = {
            'amazon': amazon_url,
        }
        return data[source]

    def valid_price(self, price):
        total = 1
        for currency in constant.CURRENCY:
            total *= price.find(currency)
        if total == 0:
            return True
        else:
            return False

    def get_amazon_data(self, data, html):
        goods_div = html('#atfResults')
        if not goods_div:
            return data
        i = 0
        for goods_li_data in goods_div('li'):
            goods_li = pq(pq(goods_li_data).html())
            goods_data = pq(
                pq(goods_li('.a-fixed-left-grid-inner')).html()
            )
            if goods_data:
                goods_img = pq(pq(goods_data('.a-col-left')).html())
                goods_url = pq(goods_img('a')).attr('href')
                goods_small_img_url = pq(goods_img('img')).attr('src')

                goods_info = pq(pq(goods_data('.a-col-right')).html())
                goods_title_div = pq(goods_info('.a-spacing-small').html())
                goods_title = pq(goods_title_div('a')).attr('title')
                goods_price_div = pq(goods_info('.a-span7').html())
                goods_price_divs = goods_price_div('.a-spacing-none')
                if len(goods_price_divs) > 1:
                    goods_price_second = goods_price_divs[1]
                    goods_price_div_a = pq(pq(goods_price_second).html())
                else:
                    goods_price_div_a = pq(
                        goods_price_div('.a-spacing-none').html()
                    )
                goods_price = goods_price_div_a('a').text()
                goods_des_div = pq(goods_info('.a-span5').html())
                goods_des = pq(
                    goods_des_div('.a-text-bold').nextAll()
                ).text()

                img_params = goods_small_img_url.split('_AC_US160_.jpg')
                img_large_params = '_SX425_.jpg'
                goods_large_img_url = img_params[0]+img_large_params
                goods_price_status = self.valid_price(goods_price)
                if goods_price and goods_title and goods_price_status:
                    data['results'][i] = {}
                    data['results'][i]['url'] = constant.SINGLE_URL+goods_url
                    data['results'][i]['goods_s_img_url'] = goods_small_img_url
                    data['results'][i]['goods_l_img_url'] = goods_large_img_url
                    data['results'][i]['goods_title'] = goods_title
                    data['results'][i]['goods_price'] = goods_price
                    data['results'][i]['goods_des'] = goods_des
                    i += 1
        goods_page_div = html('#bottomBar')
        goods_pages = []
        goods_cur_page = int(
            pq(pq(goods_page_div('.pagnCur')).html()).text()
        )

        goods_pages.append(goods_cur_page)
        data['cur_page'] = [goods_cur_page]

        for goods_page_data in goods_page_div('.pagnLink'):
            goods_page = int(pq(pq(goods_page_data).html()).text())
            goods_pages.append(goods_page)

        goods_last_page = pq(
            pq(goods_page_div('.pagnDisabled')).html()
        ).text()
        if goods_last_page:
            goods_pages.append(int(goods_last_page))
        data['pages'] = sorted(goods_pages)
        return data

    def get_data(self, url, source):
        r = requests.get(url)
        data = {}
        if r.status_code == 200:
            data['results'] = {}
            html = pq(r.text)
            if source == 'amazon':
                data = self.get_amazon_data(data, html)
            if not data['results']:
                data = {}
            return data
        else:
            return data

    def get(self, request, format=None):
        if request.GET.get('page'):
            page = request.GET.get('page')
        else:
            page = 1

        if request.GET.get('source'):
            source = request.GET.get('source')
        else:
            source = 'amazon'

        if request.GET.get('keywords'):
            keywords = request.GET.get('keywords').encode('utf8')
        else:
            keywords = 'iphone'

        url = self.get_url(keywords, page, source)
        data = self.get_data(url, source)
        # try again
        if not data:
            data = self.get_data(url, source)

        return Response(data)


class Single(APIView):

    def get_amazon_data(self, data, html):
        goods_left_col = html('#leftCol')
        if goods_left_col:
            goods_center_col = html('#centerCol')
            goods_img_div = pq(
                pq(goods_left_col('#main-image-container')).html()
            )
            goods_img_url = pq(goods_img_div('img:first')).attr('src')
            goods_title = pq(goods_img_div('img:first')).attr('alt')
            goods_price = pq(
                pq(goods_center_col('#priceblock_ourprice')).html()
            ).text()
            data['goods_price'] = goods_price
            data['goods_title'] = goods_title
            data['goods_img_url'] = goods_img_url
        return data

    def get_data(self, url, source):
        r = requests.get(url)
        data = {}
        if r.status_code == 200:
            html = pq(r.text)
            if source == 'amazon':
                data = self.get_amazon_data(data, html)
            return data
        else:
            return data

    def get(self, request, format=None):
        if request.GET.get('url'):
            url = request.GET.get('url')
        else:
            return Response({})

        if request.GET.get('source'):
            source = request.GET.get('source')
        else:
            source = 'amazon'

        data = self.get_data(url, source)
        # try again
        if not data:
            data = self.get_data(url, source)
        if data:
            goods = Goods(
                title=data['goods_title'],
                price=data['goods_price'],
                image_link=data['goods_img_url']
            )
            goods.save()
        url_data = {'url': url}
        return Response(url_data)
