import asyncio
import multiprocessing

from sb_voice_dev.client import main


def start_client():
    asyncio.run(main())


if __name__ == "__main__":
    number_of_clients = 100  # Number of clients you want to run
    processes = []

    for _ in range(number_of_clients):
        process = multiprocessing.Process(target=start_client)
        process.start()
        processes.append(process)

    for process in processes:
        process.join()
