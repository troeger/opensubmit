from threading import Thread


def run_parallel(num, func):
    threads = []
    results = []

    def wrapper():
        result = func()
        results.append(result)

    for i in range(num):
        threads.append(Thread(None, wrapper))

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    return results
