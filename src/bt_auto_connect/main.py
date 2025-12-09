#!/usr/bin/env uv
import asyncio

from .bt_auto_connect import bt_auto_connect


def main():
    # TODO: remove try except after testing
    try:
        asyncio.run(bt_auto_connect())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
