# okserver
## a simple and very high performance python framework , powered by epoll, no depending on tonado/django/flask...

```
#usage is simple
import okserver.okserver as ok


def main():
    pass


if __name__ == '__main__':
    server = ok.Server(main)
    server.start('', 2222)


```

![](http://ww1.sinaimg.cn/large/73618a2bly1frs2g78jvbj217a0uc0yu.jpg)

Aliyun ECS:
1 X Intel(R) Xeon(R) Platinum 8163 CPU @ 2.50GHz
2GB memory



