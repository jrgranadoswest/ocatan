import asyncio
import argparse
import websockets
from BoardConnect import chat

def main():
    parser = argparse.ArgumentParser(description="Conquerors of Catan")

    #  # Argument to specify the JSON file path
    #  parser.add_argument('test_arg', help='Test args')

    # Optional arguments
    parser.add_argument('-t', '--test', type=int, help='just testing')

    args = parser.parse_args()

    if args.test:
        print(f"test ok {args.test}")

    # Start websocket server
    start_server = websockets.serve(chat, 'localhost', 8080)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()



if __name__ == "__main__":
    main()

