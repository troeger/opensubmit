from threading import Thread

def run_parallel(num, func):
    threads = []
    results = []

    def wrapper():
        result=func()
        results.append(result)

    for i in range(num):
        threads.append(Thread(None, wrapper))
    list(map(lambda x: x.start(),threads))   
    list(map(lambda x: x.join(),threads))  
    return results 
