#!/usr/bin/env python
#*-* coding: utf-8
# Website-Scraper um eigene Informationen und die von Freunden aus studivz
# zu extrahieren. Siehe http://studivz.irgendwo.org/goodbye/
#
# Lizenz: GNU-AGPL-3.0
# Copyright: Hagen Fritsch, 2011

from xml.dom.minidom import parse, parseString
from mechanize import Browser
from BeautifulSoup import BeautifulSoup
import json, re
import os.path
from datetime import datetime
import time
import zipfile

cdata = re.compile(r'\<\!\[CDATA\[.+?\]\]\>')
clean_webpage = lambda data: cdata.sub('', data) #remove freaky stuff that breaks the parser

def get_content(node):
    "hacky hack to get the innerContent of a node as unicode"
    if node is None: return None
    return u''.join(map(unicode, node.contents))

def get_number_of_pages(soup):
    """
    reads a page's pager information to acquire the number of available sites
    """
    pager = soup.find('div', {'class': 'obj-navigation text-right'})
    if not pager:
        pager = soup.find('div', {'class': 'obj-pager'})
    if not pager: return 0
    try:
        return int(pager.findChildren()[-1]['title'])
    except IndexError: #pager there, but no content
        return 0

def date_parser(date):
    """
    parses a studivz-date in form of "am 07.04.2010 um 21:19 Uhr"
    and returns a datetime object
    """
    return datetime.strptime(date,'am %d.%m.%Y um %H:%M Uhr').isoformat()

def profile_parser(soup, storage):
    """
    parse a profile page to return structured key-value pairs
    """
    ret = {}    
    
    for info in soup.findAll('dl', {'class': 'obj-keyValueList'}):
        group = info.get('id', None)
        keys = [get_content(i).strip().strip(':').lower() for i in info.findAll('dt')]
        vals = [get_content(i).strip() for i in info.findAll('dd')]
        ret[group] = dict(zip(keys, vals))
    
    #post processing
    #general = ret['Mod-Profile-Information-General']
    #if 'Geburtstag' in general: general['Geburtstag'] = datetime.strptime(general['Geburtstag'][:10], '%d.%m.%Y')

    groups = soup.find('div', {'id': 'Mod-Groups-Snipplet'})
    if groups:
        for a in groups.findAll('a'):
            id, name = os.path.basename(a['href']), get_content(a)
            storage.add_group_information(id, name=name)
            ret.setdefault('groups', []).append(id)
    
    return ret

def get_pinboard_posts(soup, storage):
    """
    parse a pinboard page to extract messages
    """
    ret = []
    
    for comment in soup.findAll('div', {'class': 'comment'}):
        msg    = get_content(comment.find('div', {'class': 'pinboard-entry-text'})).strip()
        msg    = msg.replace("\n", "").replace("<br />", "\n") #simple processing
        sender = comment.find('a', {'class': 'profile'})
        if sender: # otherwise gelöschte perso
            id, name = os.path.basename(sender['href']), get_content(sender)
            storage.add_profile_information(id, name=name)
        date   = get_content(comment.find('span', {'class': 'datetime'})).strip() 
        ret.append({'message': msg, 'sender': id if sender else None, 'datetime': date_parser(date)})
    
    return ret

def get_photos(soup, storage, friend_id=None, album_id=None):
    """
    parse a photo album page and return album-information and the list of pictures
    """
    kommentare = re.compile('(\d+) Kommentar')
    ret        = []
    info       = {}

    desc = soup.find('p', {'id': 'album-description'})
    if desc: info['description'] = get_content(desc).strip()
    info['title']       = get_content(soup.find('div', {'class': 'photo-list'}).find('h2')).strip()
    info_pager = soup.findAll('div', {'class': 'info-pager'})
    if info_pager:
        ort = info_pager[-1].find('div', {'class': 'no-float'})
        if ort and 'Ort:' in get_content(ort):
            info['ort'] = ort.contents[-1].strip()

    if friend_id and album_id:
        storage.add_album_information(album_id, owner=friend_id, **info)
    
    photos = soup.find('ul', {'class': 'photos'})
    if photos:
      for photo in photos.findAll('li'):
        url      = photo.find('img')['src']
        data = {'url': url.replace('-m.jpg', '.jpg')}
        
        caption  = photo.find('div', {'class': 'caption'})
        comments = kommentare.search(get_content(caption))
        comments = int(comments.group(1)) if comments else 0
        captions = caption.findAll('span')
        album    = {}
        for node in captions:
            text = get_content(node)
            a = node.find('a')
            if a and "Album" in text:
                album['name']       = get_content(a)
                album['id']         = os.path.basename(a['href'])
            elif a and "von" in text:
                id, name = os.path.basename(a['href']), get_content(a)
                storage.add_profile_information(id, name=name)
                album['owner']      = id
            else:
                data['caption']     = text.strip()
        
        if comments: data['comments'] = comments
        if album:
            data['album']    = album['id']
            storage.add_album_information(**album)
        ret.append(data)
    
    return ret

def get_photo_album_ids(soup):    
    #remove albums of your friends referenced at your own album list
    #friends_albums = soup.find('div', {'class': 'overview-friends-snipplet'})
    #if friends_albums: friends_albums.extract()

    photoalbums = soup.find('ul', {'class': 'photoalbums'})
    if not photoalbums: return []
    album_ids = [i['id'].replace('albumid:', '') for i in photoalbums.findChildren('li')]
    return album_ids

class LoginException(Exception): pass
class DataException(Exception): pass
class CaptchaException(Exception): pass

class StudiVZ:
    host = "http://www.studivz.net"
    def __init__(self, mail, pw, config=None):
        self.mail = mail
        self.pw = pw
        self.br = None
        self.friends = None
        self.profiles = {}
        self.groups = {}
        self.zip = zipfile.ZipFile("%s.zip" % mail, 'a', compression=zipfile.ZIP_STORED)
        if config:
            self.load_info(open(config))

    def add_album_information(self, id, owner, **kwargs):
        album = self.profiles.setdefault(owner, {}).setdefault('albums', {}).setdefault(id, {})
        album.update(kwargs)

    def add_profile_information(self, id, **kwargs):
        profile = self.profiles.setdefault(id, {})
        profile.update(kwargs)

    def add_group_information(self, id, **kwargs):
        group = self.groups.setdefault(id, {})
        group.update(kwargs)

    def login(self):
        """
        fill out the login form and submit
        stores a reference to the browser in self.br
        """
        br = Browser()
        br.open(self.host)
        br.select_form(nr=0)
        br['email'] = self.mail
        br['password'] = self.pw
        br['ipRestriction'] = []
        res = br.submit().read()
        if not "Meine Startseite" in res:
            raise LoginException()
        soup = BeautifulSoup(clean_webpage(res))
        self.id = os.path.basename(soup.find('a', {'class': 'profile-link float-left'})['href'])
        self.br = br
    
    def load_site(self, args, no_soup=False):
        """
        loads a page on the hosts site, saves it in the tar
        and parses it using BeautifulSoup
        """
        try:
            res = self.zip.read(args)
        except KeyError:
            res = self.br.open(self.host + "/" + args).read()
            if "Sicherheits-Abfrage" in res:
                self.last_res = (res, None) #store the page for debuging
                raise CaptchaException()
            self.zip.writestr(args, res)

        if no_soup:
            return res
        soup = BeautifulSoup(clean_webpage(res))
        self.last_res = (res, soup)
        return res, soup

    def read_paginated_data(self, args, extract_data):
        """
        read paginated data by iterating over all pages
        calling 'extract_data(soup)' on each to extract information
        and returning the combined list of these
        """
        data, soup = self.load_site(args)
        pages = get_number_of_pages(soup)
        print "%s\t%d pages" % (args, pages)
        
        ret = extract_data(soup)
        def update(a, x):
            if a is None: return
            if type(a) == dict:
                a.update(x)
            else:
                a += x

        for page in xrange(2, pages+1):
            data, soup = self.load_site(args + "/p/%d" % page)
            res = extract_data(soup)
            update(ret, res)
            if len(res) == 0:
                if 'Tags' in args: # there might be less tags than initially shown
                    return ret
                raise DataException("No elements read :( captcha?")
            print "%s\tpage % 2d/%d\textracted %d elements" % (args, page, pages, len(res))

        return ret

    def update_friends_list(self):
        """
        retrieves the friendlist
        """
        data, soup = self.load_site("Messages/WriteMessage")
        js = soup.find('input', {'id': 'friendList'})
        self.friends = json.loads(js['value'])

    def get_friends_list(self):
        """
        returns the friendlist updating it if not yet loaded
        """
        if not self.friends:
            self.update_friends_list()
        return self.friends

    def get_profile(self, friend_id):
        """
        loads a profile and stores it
        """
        data, soup = self.load_site("Profile/" + friend_id)
        self.profiles.setdefault(friend_id, {}).update(profile_parser(soup, self))

    def read_pinboard_page(self, friend_id, page=1):
        return self.load_site("Pinboard/%s/p/%d" % (friend_id, page))

    def get_pinboard(self, friend_id):
        """
        reads the complete pinboard and parses the messages storing them in the friend_list

        get_friend_list() has to be called beforehand
        """
        posts = self.read_paginated_data("Pinboard/" + friend_id, lambda soup: get_pinboard_posts(soup, self))
        self.profiles.setdefault(friend_id, {})['pinboard'] = posts

    def get_own_photo_albums(self):
        """
        downloads each of this users photo albums
        needs special handling, because the page displays all your friends photo albums
        """
        album_ids = self.read_paginated_data("Photos/Album/" + self.id, get_photo_album_ids)
        
        for album_id in album_ids:
            res = self.get_photo_album(friend_id, album_id)

    def get_photo_albums(self, friend_id):
        """
        iterates over all photo albums of this user
        saving all album information and pictures
        (does not iterate over each photo page, thus comments and long descriptions are not [yet] saved)
        """
        album_ids = self.read_paginated_data("Photos/Friends/" + friend_id, get_photo_album_ids)

        for album_id in album_ids:
            res = self.get_photo_album(friend_id, album_id)

    def get_photo_album(self, friend_id, album_id):
        """
        reads a certain album
        and saves its information
        """
        photos = self.read_paginated_data("Photos/Album/%s/%s" % (friend_id, album_id), lambda soup: get_photos(soup, self, friend_id, album_id))
        self.profiles.setdefault(friend_id, {}).setdefault('albums', {}).setdefault(album_id, {})['photos'] = photos

    def get_photo_tags(self, friend_id):
        """
        reads all pictures in which the user is tagged
        """
        photos = self.read_paginated_data("Photos/Tags/%s/%s" % (friend_id, friend_id), lambda soup: get_photos(soup, self, friend_id))
        self.profiles.setdefault(friend_id, {})['links'] = photos

    def print_all_images(self, out_file):
        for p in self.profiles.itervalues():
            for a in p.get('albums', {}).itervalues():
                for i in a.get('photos', []):
                    out_file.write(i['url']+"\n")
            for i in p.get('links', []):
                out_file.write(i['url']+"\n")

    def dump_info(self, out_file):
        data = {'profiles': self.profiles, 'groups': self.groups, 'friends': self.friends, 'id': self.id}
        json.dump(data, out_file, indent=4)

    def load_info(self, in_file):
        data = json.load(in_file)
        self.profiles = data['profiles']
        self.groups = data['groups']
        self.friends = data['friends']

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print """usage: %s email password [what]
    what := profiles,tags,albums,pinboards (any combination seperated by ',')""" % sys.argv[0]
        sys.exit(0)

    email    = sys.argv[1]
    password = sys.argv[2]
    downloads = ['profiles'] if len(sys.argv) < 3 else sys.argv[3].split(",")
    config   = None
    if os.path.exists("%s.json" % email):
        config = "%s.json" % email

    s = StudiVZ(sys.argv[1], sys.argv[2], config)
    s.login()
    try:
        print "downloading your own information..."
        s.get_friends_list()
        s.get_profile(s.id)
        s.get_photo_tags(s.id)
        s.get_own_photo_albums()
        s.get_pinboard(s.id)
        if 'profiles' in downloads:
            num_friends = len(s.get_friends_list())
            print "downloading %d friend profiles" % num_friends
            for friend in s.friends:
                print s.friends[friend].get('name', friend)
                s.get_profile(friend)
        if 'tags' in downloads:
            print "downloading tagged images of your friends"
            for friend in s.friends:
                s.get_photo_tags(friend)
        if 'albums' in downloads:
            print "downloading photo albums of your friends"
            for friend in s.friends:
                s.get_photo_albums(friend)
        if 'pinboards' in downloads:
            print "downloading pinboard messages of your friends"
            for friend in s.friends:
                s.get_pinboard(friend)
    except BaseException: #also catch KeyboardInterrupts
        print "An error occurred. Saving state."
        s.zip.close()
        s.dump_info(open("%s.json" % email, "w"))
        raise

    print "Download successful, saving state..."
    s.zip.close()
    s.dump_info(open("%s.json" % email, "w"))
    s.print_all_images(open("%s.img-list" % email, "w"))
    print "completed, you can now continue and download images from %s.img-list" % email
    print "you might also want to compress or delete the intermediate data:"
    print "   $ gzip %s.zip" % email
    print "Your results are stored in %s.json" % email
