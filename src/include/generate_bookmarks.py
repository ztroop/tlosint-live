import argparse
import asyncio
import sys

import aiohttp
import yaml
from aiohttp.client_exceptions import (
    ClientConnectorError,
    ClientConnectorSSLError,
    ClientResponseError,
)
from aiohttp.http_exceptions import BadHttpMessage
from loguru import logger


async def verify_bookmark(link, session):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.90 Safari/537.36"
        }
        async with session.get(link, headers=headers) as resp:
            if resp.status == 200 or resp.status == 302:
                logger.info(f"✅ Resolved: {link}")
            else:
                logger.error(f"❌ Unresolved: ({resp.status}) {link}")
    except BadHttpMessage:
        logger.error(f"❌ Invalid HTTP Message: {link}")
    except ClientResponseError:
        logger.error(f"❌ Invalid Character in Header: {link}")
    except ClientConnectorSSLError as err:
        logger.error(f"❌ Invalid SSL Response: {link} ({err})")
    except ClientConnectorError as err:
        logger.error(f"❌ Cannot Connect: {link} ({err})")
    except AssertionError:
        pass


async def write_bookmarks(nodes, level, out):
    async with aiohttp.ClientSession() as session:
        tasks = []

        indent = "    " * level
        out.write(indent + "<DL><p>\n")
        for node in nodes:
            if "folder" in node:
                out.write(indent + "<DT><H3>" + node["folder"] + "</H3>\n")
                await write_bookmarks(node["bookmarks"], level + 1, out)
            elif SEPARATOR_NAME == node["name"] and not "bookmarks" in node:
                out.write(indent + "<HR>\n")
            elif "url" in node:
                tasks.append(
                    asyncio.ensure_future(verify_bookmark(node["url"], session))
                )
                out.write(indent + "<DT><A")
                out.write(' HREF="' + node["url"] + '"')

                if "icon" in node:
                    out.write(' ICON="' + node["icon"] + '"')

                if tag_all or "tags" in node:
                    tags = []
                    if tag_all:
                        tags.append(tag_all)
                    if "tags" in node:
                        tags.extend(node["tags"])
                    out.write(' TAGS="' + ",".join(tags) + '"')

                out.write(">")
                out.write(node["name"])
                out.write("</A>")
                out.write("\n")

                if "description" in node:
                    out.write(indent + "<DD>" + node["description"] + "\n")

        out.write(indent + "</DL><p>\n")
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--tag", help="add a tag to all bookmarks")
    parser.add_argument("-o", "--output", help="the bookmark output file")
    parser.add_argument("inputfile", help="the bookmark input file")
    args = parser.parse_args()

    bookmark_data = yaml.safe_load(open(args.inputfile))

    out = sys.stdout

    SEPARATOR_NAME = "---"

    tag_all = args.tag

    if args.output:
        out = open(args.output, "w")

    out.write(
        """<!DOCTYPE NETSCAPE-Bookmark-file-1>
	<!-- This is an automatically generated file.
		It will be read and overwritten.
		DO NOT EDIT! -->
	<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
	<TITLE>Bookmarks</TITLE>
	<H1>Bookmarks</H1>

	"""
    )

    asyncio.run(write_bookmarks(bookmark_data, 0, out))

    out.flush()
