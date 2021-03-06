from lxml import etree
import re

f = open ('result3.xml', 'r')
xml = f.read ()
f.close ()

root = etree.fromstring (xml)
c = 0

#f = open ('data1_validurl.txt', 'r')
#urls = f.readlines ()
#f.close ()

#print "<dblp>"
affns = {}
key = []

for article in root.xpath ('*'):
    
    p = re.compile (r'(?P<name>.*)\((?P<affn>.*)\)')
    rauthors = article.xpath ('rauthor')
    for rauthor in rauthors:
        m = p.search (rauthor.text)
        if m:
            affn = unicode (m.group ('affn')).encode ('latin-1')
            count = 0
            if affns.has_key (affn):
                affns[affn] = affns[affn] + 1
            else:
                key.append (affn)
                affns[affn] = 1
                #print unicode (affn).encode ('latin-1')
    
    #print etree.tostring (article, pretty_print = True)

key.sort ()

pairs = []

for i in key:
    pairs.append ((-affns[i], i))

pairs.sort ()

for freq, affn in pairs:
    print affn + '\t' + str (-freq)

#print "</dblp>"
