#! coding=utf-8

import urllib2, urllib, re, json
import lxml.html.soupparser as sp

from mechanize import Browser
from lxml import etree
from data import Paper, Author

class PaperFetcher:
    """
    TODO
    """
   
    def __wrapper (self, url):
        path = urllib.quote(url, safe="")
        return "http://pkudblp1.appspot.com/route?url=%s" % path
    
    
    def __init__ (self):
        # set up mechanize Browser
        self.br = Browser ()

        # enable proxy?
        enable_proxy = False

        # set up parameters of the browser
        self.br.set_handle_equiv (True)
        self.br.set_handle_redirect (True)
        self.br.set_handle_referer (True)
        self.br.set_handle_robots (False)

        if enable_proxy:
           self.br.set_proxies({"http": "http://localhost:8087" }) 

        # disguise as firefox browser
        self.br.addheaders = [
                  ("User-Agent", "Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0"), 
                  ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                  ("Accept-Language", "en-us,en;q=0.5"), 
                  ("Accept-Charset", "gb18030,utf-8;q=0.7,*;q=0.7")]

        proxy_handler = urllib2.ProxyHandler ({'http' : 'http://localhost:8087'})

        # set up urllib2 opener
        if enable_proxy:
            self.op = urllib2.build_opener (proxy_handler)
        else:
            self.op = urllib2.build_opener ()

        # disguise as firefox browser
        self.op.addheaders = [
                  ("User-Agent", "Mozilla/5.0 (X11; Linux i686; rv:5.0) Gecko/20100101 Firefox/5.0"), 
                  ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
                  ("Accept-Language", "en-us,en;q=0.5"), 
                  ("Accept-Charset", "gb18030,utf-8;q=0.7,*;q=0.7")]

    
    def __deljs_html (self, html):
        # get rid of embedded javascript 
        while html.find ("<script") != -1:
            a = html.find ("<script")
            b = html.find ("/script>")
            html = html[:a] + html[b + 8:]
        return html
 

    def __get_paperentry_from_acm (self, title, authors):
        QUERY_URL = 'http://dl.acm.org/advsearch.cfm'

        self.br.open (self.__wrapper (QUERY_URL))
        
        # this query form does not have id attribute, nr=0 means the first form
        self.br.select_form (nr=0)
   
        # termzone is a multi choice dropdown menu, the value should be a list
        self.br.form['termzone'] = ['Title']
        self.br.form['allofem'] = title
        self.br.form['peoplezone'] = ['Author']
        self.br.form['people'] = authors 
        self.br.form['peoplehow'] = ['and']
        resp_body = self.__deljs_html (self.br.submit ().read ())

        # check if the rearch result is not empty
        if resp_body.find ('was not found') == -1:
            root = sp.fromstring (resp_body)

            # select the first entry in search result
            entry_url = root.xpath ("//a[@class='medium-text' and @target='_self' and \
                starts-with (@href, 'citation.cfm')]/@href")[0]
            return 'http://dl.acm.org/' + entry_url
        else:
            return ""


    def __get_paper_from_acm (self, entry_url):
        resp_body = self.__deljs_html (self.op.open (self.__wrapper (entry_url)).read ())
        root = sp.fromstring (resp_body)

        divmain = root.xpath ("//div[@id='divmain']")[0]

        title = divmain.xpath ("div/h1/strong")[0].text
        
        # UPDATE: NO NEED FOR ABSTRACT
        # use regex to extract abstract link
        #abst_url = re.compile (r"tab.abstract.cfm[^']*").search (resp_body).group (0)
        #abst_url = 'http://dl.acm.org/' + abst_url
        #abst_body = self.op.open (abst_url).read ()
        
        # extract all text node from this dom tree
        #abst = ''.join (sp.fromstring (abst_body).xpath ('//div/p/div/p/descendant-or-self::*/text()'))
        
        # instantiate a Paper class
        paper = Paper (title)

        # locate the author table block
        author_table = divmain.xpath ("table/tr/td/table")[1]

        # add each author
        for author_row in author_table.xpath ('tr'):
            name = author_row.xpath ('td/a/text()')[0]
            
            # if the text is in tag <a>, then it has a link to this affiliation
            if len (author_row.xpath ('td/a/small/text()')) > 0:
                affn = author_row.xpath ('td/a/small/text()')[0]
            elif len (author_row.xpath ('td/small/text()')) > 0:
                affn = author_row.xpath ('td/small/text()')[0]
            else:
                affn = ""

            paper.add_author (Author (name, affn))

        return paper

    
    def __preprocess_query (self, title, authors):
        title = title.replace (':', ' ').replace ('-', ' ')
        authors = authors.replace (':', ' ').replace ('-', ' ')

        # preprocess the title and authors
        a_forbid = re.compile ('[\W\d]')

        # strip all non-english character names from authors
        new_authors = ""
        for entity in authors.split (' '):
            if not a_forbid.search (entity):
                new_authors = new_authors + " " + entity

        # assuming title does not contain non-alphanumeric
        t_forbid = re.compile ('\W')

        title = title.rstrip ('.')
        new_title = ""
        for entity in title.split (' '):
            if not t_forbid.search (entity):
                new_title = new_title + " " + entity
        
        title = new_title
        authors = new_authors
        #print "new param: Title (%s)  authors (%s)" % (title, authors)
 
        return (title, authors)


    def get_paper_from_acm (self, title, authors):
        (title, authors) = self.__preprocess_query (title, authors)       
        
        entry_url = self.__get_paperentry_from_acm (title, authors)
        if entry_url:
            return self.__get_paper_from_acm (entry_url)
        else:
            return None


    def __get_paperentry_from_ms (self, title, authors):
        QUERY_URL = 'http://academic.research.microsoft.com/'
        print "ENTER"
        self.br.open (QUERY_URL)
        
        # select the query box which name is "aspnetForm"
        self.br.select_form (name='aspnetForm')

        # construct query according to their query language
        self.br.form['ctl00$SearchHeader$SearchForm$txtQuery'] = \
            'author:(' + authors + ') ' + '' + title + ''
        resp_body = self.__deljs_html (self.br.submit ().read ())
        print "SUBMIT"

        # if search result is not empty
        if resp_body.find ('We did not find any result related to') == -1:
            root = sp.fromstring (resp_body)
            print "FINISHED"
            # select the first entry in search result
            entry_url = root.xpath ("//a[@id='ctl00_MainContent_PaperList_ctl01_Title']/@href")[0]
            return 'http://academic.research.microsoft.com/' + entry_url
        else:
            return ""

    
    def __get_paper_from_ms (self, entry_url):
        resp_body = self.__deljs_html (self.op.open (entry_url).read ())
        root = sp.fromstring (resp_body)
 
        title = root.xpath ("//span[@id='ctl00_MainContent_PaperItem_title']")[0].text
        #abst = root.xpath ("//span[@id='ctl00_MainContent_PaperItem_snippet']")[0].text

        # instantiate a Paper class
        paper = Paper (title)

        # locate the div block for the paper description
        paper_div = root.xpath ("//div[@id='ctl00_MainContent_PaperItem_divPaper']/div")[1]
       
        for author_url in paper_div.xpath ("a[@class='author-name-tooltip']/@href"):
            # print author_url
            paper.add_author (self.__get_author_from_ms (author_url))

        return paper


    def __get_author_from_ms (self, entry_url):
        author_id = entry_url.split ('/')[-2]
        entry_url = "http://academic.research.microsoft.com/io.ashx?authorID=%s" % author_id
        resp_body = self.op.open (entry_url).read ()
        json_obj = json.loads (resp_body)
        
        name = json_obj['DisplayName']
        if json_obj['Affiliation']:
            affn = json_obj['Affiliation']['FullName']
        else:
            affn = ''
        print "Finished author"
        return Author (name, affn) 


        # OLD ONE: FETCH OFFICIAL AUTHOR PAGE
        root = sp.fromstring (resp_body)

        name = root.xpath ("//span[@id='ctl00_MainContent_AuthorItem_authorName']")[0].text
        aff_nodes = root.xpath ("//a[@id='ctl00_MainContent_AuthorItem_affiliation']")
        
        # make sure the author page has affiliation 
        if len (aff_nodes) > 0:
            affn = aff_nodes[0].text
        else:
            affn = ""

        return Author (name, affn)

    
    def get_paper_from_ms (self, title, authors):
        entry_url = self.__get_paperentry_from_ms (title, authors)
        print "Finished paper entry"
        if entry_url:
            return self.__get_paper_from_ms (entry_url)
        else:
            return None


    def test_private_getpe_acm (self):
        title =  'Promotion Analysis in multi-dimensional space'
        authors = 'Tianyi Wu, Dong Xin, Qiaozhu Mei, Jiawei Han'
        print self.__get_paperentry_from_acm (title, authors)

    
    def test_private_getp_acm (self):
        url = 'http://dl.acm.org/citation.cfm?' + \
            'id=1687627.1687641&coll=DL&dl=GUIDE&CFID=99867254&CFTOKEN=89989886'
        print self.__get_paper_from_acm (url)

    
    def test_getp_acm (self):
        #authors = 'Jonathan J. Hoch Adi Shamir'
        #title = 'On the Strength of the Concatenated Hash Combiner When All the Hash Functions Are Weak'
        #authors = 'Adnan Vora Mikhail Nesterenko'
        #title = 'Secure Location Verification Using Radio Broadcast.'
        authors = 'Henrique Moniz Nuno Ferreira Neves Miguel Correia Paulo Veríssimo'
        title = 'RITAS: Services for Randomized Intrusion Tolerance.'
        print self.get_paper_from_acm (title, authors)


    def test_private_getpe_ms (self):
        authors = 'Zhenjie Zhang Beng Chi Ooi'
        title = 'Similarity Search on Bregman Divergence: Towards Non-Metric Indexing'
        print self.__get_paperentry_from_ms (title, authors)


    def test_private_getp_ms (self):
        url = 'http://academic.research.microsoft.com/Publication/2181095/' + \
        'comparing-gene-expression-networks-in-a-multi-dimensional-space-to-extract-similarities-and'
        print self.__get_paper_from_ms (url)


    def test_private_geta_ms (self):
        url = 'http://academic.research.microsoft.com/Author/3501073/zhenjie-zhang'
        print self.__get_author_from_ms (url)


    def test_getp_ms (self):
        title = 'Application and evaluation of spatiotemporal enhancement of live aerial video using temporally local mosaics.'
        authors = 'Bryan Damon Cameron Michael Nathan Daniel Dennis'
        print self.get_paper_from_ms (title, authors)

if __name__ == '__main__':
    pf = PaperFetcher ()
    #pf.test_getpe_acm ()
    pf.test_getp_ms ()
    #pf.test_getp_ms ()
    #pf.test_getp_ms ()
    #pf.test_geta_ms ()

    #fetch_dl_acm ()
    #fetch_ms_academic ()
    #fetch_ms_author ()
