import re
import datetime
import json
import psycopg2
import xml.etree.ElementTree as ET


def str_escape(orig: str) -> str:
    """
    Escapes string for PostgreSQL

    :param orig: Original
    :return: Escaped
    """
    return re.sub(r"'", r"''", orig)


async def get_feed_as_dict(text, service_name):
    res = dict(items=list())
    namespaces = dict()
    root = ET.fromstring(text)
    feed_tag_mods = dict(lastBuildDate='last_build_date', pubDate='pub_date')
    feed_item_tag_mods = dict(pubDate='pub_date')
    feed_discard_tags = ['link']
    feed_item_discard_tags = list()
    if service_name == 'www.nu.nl':
        namespaces['http://www.w3.org/2005/Atom'] = 'atom'
        namespaces['http://purl.org/dc/elements/1.1/'] = 'dc'
        namespaces['http://search.yahoo.com/mrss/'] = 'media'
        date_format = "%a, %d %b %Y %H:%M:%S %z"
        feed_tag_mods['atom:logo'] = 'image'
        feed_item_tag_mods['atom:link'] = 'links'
        feed_item_tag_mods['dc:creator'] = 'creator'
        feed_item_tag_mods['dc:rights'] = 'rights'
        feed_discard_tags.extend(['atom:link'])
    elif service_name == 'feeds.feedburner.com':
        namespaces['http://www.w3.org/2005/Atom'] = 'atom10'
        namespaces[
            'http://rssnamespace.org/feedburner/ext/1.0'] = 'feedburner'
        namespaces['http://www.w3.org/1999/xhtml'] = 'xhtml'
        date_format = "%a, %d %b %Y %H:%M:%S %Z"
        feed_tag_mods['webMaster'] = 'web_master'
        feed_discard_tags.extend(['xhtml:meta',
                                  'feedburner:info',
                                  'atom10:link'])
        feed_item_discard_tags.extend(['comments'])
    else:
        return dict()
    chanel = root[0]
    for child_ele in chanel:
        if child_ele.tag == 'item':
            item_data = dict(category=list())
            for item_elem in child_ele:
                prefix, has_namespace, postfix = item_elem.tag.partition('}')
                if has_namespace:
                    key = namespaces.get(prefix.replace("{", ""), "NSPL")
                    item_elem.tag = f'{key}:{postfix}'
                if item_elem.tag in feed_item_tag_mods:
                    item_elem.tag = feed_item_tag_mods[item_elem.tag]
                if item_elem.tag in feed_item_discard_tags:
                    continue

                if item_elem.tag == 'pub_date' and date_format:
                    item_data[item_elem.tag] = datetime.datetime.strptime(
                        item_elem.text, date_format)
                elif item_elem.tag == 'category':
                    if service_name == 'feeds.feedburner.com':
                        cleaned = re.sub(r'^.*:\ ', '', item_elem.text)
                        cleaned = re.sub(r'\ /\ ', '/', cleaned)
                        item_data[item_elem.tag].extend(cleaned.split('/'))
                    else:
                        item_data[item_elem.tag].append(item_elem.text)
                elif item_elem.tag == 'enclosure':
                    item_data[item_elem.tag] = item_elem.attrib['url']
                elif item_elem.tag == 'links' and not item_elem.text:
                    tag_name = f'{item_elem.attrib["rel"]}_{item_elem.tag}'
                    if not item_data.get(tag_name):
                        item_data[tag_name] = list()
                    href = item_elem.attrib['href']
                    item_data[tag_name].append([href, item_elem.attrib.get(
                        'title', 'No title availabe for this link.')])
                else:
                    item_data[item_elem.tag] = item_elem.text
            res['items'].append(item_data)
        else:
            prefix, has_namespace, postfix = child_ele.tag.partition('}')
            if has_namespace:
                key = namespaces.get(prefix.replace("{", ""), "NSPL")
                child_ele.tag = f'{key}:{postfix}'
            if child_ele.tag in feed_tag_mods:
                child_ele.tag = feed_tag_mods[child_ele.tag]
            if child_ele.tag in feed_discard_tags:
                continue

            if (child_ele.tag in ['last_build_date', 'pub_date']
                    and date_format):
                res[child_ele.tag] = datetime.datetime.strptime(child_ele.text,
                                                                date_format)
            elif child_ele.tag == 'ttl':
                res[child_ele.tag] = int(child_ele.text)
            elif child_ele.tag == 'image' and not child_ele.text:
                res[child_ele.tag] = child_ele.find('url').text
            else:
                res[child_ele.tag] = child_ele.text
    return res


async def push_to_db(feed_id, feed_dict, conn, uid):
    feed_data = dict()
    feed_items = list()
    if 'items' in feed_dict:
        for item in feed_dict['items']:
            item['feed_id'] = feed_id
        feed_items = feed_dict['items']
        del feed_dict['items']
        feed_data = feed_dict
    async with conn.cursor() as cur:
        if feed_data:
            update_strs = list()
            for key, value in feed_data.items():
                if isinstance(value, str):
                    update_strs.append(f"{key} = '{value}'")
                elif isinstance(value, datetime.datetime):
                    update_strs.append(f"{key} = '{value}'")
                elif isinstance(value, list):
                    update_strs.append(f"{key} = '{json.dumps(value)}'")
                else:
                    update_strs.append(f'{key} = {value}')
            await cur.execute(f'UPDATE feed SET {", ".join(update_strs)} '
                              f'WHERE id = {feed_id}')
        for feed_item in feed_items:
            values = list()
            for value in feed_item.values():
                if isinstance(value, str):
                    value = re.sub(r"\'", '\"', value)
                    values.append(f"'{str_escape(value)}'")
                elif isinstance(value, datetime.datetime):
                    values.append(f"'{value}'")
                elif isinstance(value, list):
                    fin_value = ''
                    for idx, val in enumerate(value):
                        if isinstance(val, list):
                            val_items = '","'.join(
                                [str_escape(v) for v in val])
                            fin_value = (fin_value + "{" + f'"{val_items}"'
                                         + "}")
                        else:
                            fin_value = f'"{str_escape(val)}"'
                        if idx < len(value) - 1:
                            fin_value += ','
                    values.append("'{" + fin_value + "}'")
                else:
                    values.append(f'{value}')
            keys = list(feed_item.keys())
            keys.append('create_date')
            keys.append('user_id')
            keys.append('favorite')
            keys.append('read')
            values.append(f"'{datetime.datetime.now()}'")
            values.append(f'{uid}')
            values.append(f'False')
            values.append(f'False')
            try:
                await cur.execute(f'INSERT INTO feed_item ({",".join(keys)}) '
                                  f'VALUES ({",".join(values)})')
            except psycopg2.errors.UniqueViolation:
                pass
