# okserver
## a simple and very high performance python framework , powered by epoll, no depending on tonado/django/flask...

```
#usage is simple
import okserver.okserver as ok
from model.forever_main import run_main, logger

if __name__ == '__main__':
    server = ok.Server(run_main)
    server.set_logger(logger)
    server.start('', 2222)


```

![](https://ws1.sinaimg.cn/large/73618a2bly1frrfyg2550j21xu17q7bl.jpg)

