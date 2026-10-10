import asyncio
import json
import sys

from fastmcp import Client


async def main(url: str, tool: str | None, args_json: str | None) -> None:
    async with Client(url) as client:
        for t in await client.list_tools():
            print(f"Tool:  {t.name}")

        if tool:
            args = json.loads(args_json or "{}")
            result = await client.call_tool(tool, args)
            print("Result", result.data)


if __name__ == "__main__":
    asyncio.run(
        main(
            sys.argv[1],
            sys.argv[2] if len(sys.argv) > 2 else None,
            sys.argv[3] if len(sys.argv) > 3 else None,
        )
    )
