# API网关Kong实战

主讲老师： zp

## 1.Kong介绍

Kong是一款基于OpenResty（Nginx + Lua模块）编写的高可用、易扩展的，由Mashape公司开源的API Gateway项目。Kong是基于NGINX和Apache Cassandra或PostgreSQL构建的，能提供易于使用的RESTful API来操作和配置API管理系统，所以它可以水平扩展多个Kong服务器，通过前置的负载均衡配置把请求均匀地分发到各个Server，来应对大批量的网络请求。

官网：https://konghq.com/

![avatar](https://raw.githubusercontent.com/zpnvliba/images/main/kong/1707a101967fb080)

**Kong主要有三个组件：**

1. Kong Server ：基于nginx的服务器，用来接收API请求。
2. Apache Cassandra/PostgreSQL ：用来存储操作数据。
3. Kong dashboard：官方推荐UI管理工具，当然，也可以使用 restfull 方式 管理admin api。

Kong采用插件机制进行功能定制，插件集（可以是0或N个）在API请求响应循环的生命周期中被执行。插件使用Lua编写，目前已有几个基础功能：HTTP基本认证、密钥认证、CORS（Cross-Origin Resource Sharing，跨域资源共享）、TCP、UDP、文件日志、API请求限流、请求转发以及Nginx监控。



![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/6cec96ae2df24db291a1811afa74dceb%7Etplv-k3u1fbpfcp-zoom-1.image)

### 1.1 Kong网关的特性

Kong网关具有以下的特性：

- 可扩展性: 通过简单地添加更多的服务器，可以轻松地进行横向扩展，这意味着您的平台可以在一个较低负载的情况下处理任何请求；

- 模块化: 可以通过添加新的插件进行扩展，这些插件可以通过RESTful Admin API轻松配置；

- 在任何基础架构上运行: Kong网关可以在任何地方都能运行。您可以在云或内部网络环境中部署Kong，包括单个或多个数据中心设置，以及public，private 或invite-only APIs。

  

### 1.2 Kong网关架构

![image-20210708200835615](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210708200835615.png)

1. Kong核心基于OpenResty构建，实现了请求/响应的Lua处理化；

2. Kong插件拦截请求/响应；

3. Kong Restful 管理API提供了API/API消费者/插件的管理；

4. 数据中心用于存储Kong集群节点信息、API、消费者、插件等信息，目前提供了PostgreSQL和Cassandra支持，如果需要高可用建议使用Cassandra；

5. Kong集群中的节点通过gossip协议自动发现其他节点，当通过一个Kong节点的管理API进行一些变更时也会通知其他节点。每个Kong节点的配置信息是会缓存的，如插件，那么当在某一个Kong节点修改了插件配置时，需要通知其他节点配置的变更。

   



## 2.Kong环境搭建

https://konghq.com/install/

![image-20210705213236593](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210705213236593.png)

### 2.1 基于centos7搭建

环境： PostgreSQL 9.6 + CentOS 7

#### 2.1.1 PostgreSQL

下载地址：https://www.postgresql.org/download/linux/redhat/

##### 安装命令

选择 PostgreSQL 9.6 + CentOS 7 后获得安装方式：

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard.png)

启动postgresql后查看状态：

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard-1625492380900.png)

##### 配置postgresql

为了安全以及满足 Kong 初始化的需求，需要创建一个 Linux 用户 kong，并创建对应的 PostgreSQL 用户 kong 和数据库 kong

```shell
# 创建一个 Linux 用户 `kong`
$ adduser kong

# 切换到 Linux 系统用户 `postgres`，因为它是 PostgreSQL 数据库的系统管理员
$ su postgres

# 进入 PostgreSQL 控制台
$ psql

# 设置用户 `postgres` 的密码【仅仅首次需要】
# 注意开头的 \ 必须有！
$ \password postgres 

# 创建一个 PostgreSQL 用户 `kong`，和上面创建的 Linux 用户 `kong` 对应。
# 密码 '123456' 根据自己需要生成
$ create user kong with password '123456'; 
# 创建一个 PostgreSQL 数据库 `kong`
$ create database kong owner kong;
# 将数据库 `kong` 授权给 PostgreSQL 用户 `kong`
$ grant all privileges on database kong to kong;

# 退出 PostgreSQL 控制台
$ \q
```

PostgreSQL 有四种身份认证方式：

- trust：凡是连接到服务器的，都是可信任的。只需要提供 PostgreSQL 用户名，可以没有对应的操作系统同名用户。
- password 和 md5：对于远程访问，需要提供 PostgreSQL 用户名和密码。对于本地连接，提供 PostgreSQL 用户名密码之外，还需要有操作系统访问权（用操作系统同名用户验证）。password 和 md5 的区别，就是远程访问时传输的密码是否用 md5 加密。
- ident：对于远程访问，从 ident 服务器获得客户端操作系统用户名，然后把操作系统作为数据库用户名进行登录对于本地连接，实际上使用了 peer。
- peer：对于本地访问，通过客户端操作系统内核来获取当前系统登录的用户名，并作为 PostgreSQL 用户名进行登录。

默认配置下，我们无法在本地或者远程使用 PostgreSQL 用户名和密码直接连接，因为本地使用 peer 认证方式，远程使用 ident 认证方式。解决方法比较简单，将本地和远程的认证方式修改成 trust 或者 password 即可。

修改 /var/lib/pgsql/9.6/data/pg_hba.conf 文件，注释掉所有默认配置，并添加一条 host all all 0.0.0.0/0 trust 默认，无论远程还是本地访问，任何 PostgreSQL 用户和数据库，都使用 trust 认证方式。

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard-1625492262176.png)

默认配置下，PostgreSQL 只允许本地连接，所以我们需要修改 /var/lib/pgsql/9.6/data/postgresql.conf 文件，添加 listen_address 配置项为 *，允许远程连接。

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard-1625492291456.png)

修改完成后，执行 sudo systemctl restart postgresql-9.6 命令，重启 PostgreSQL 数据库。

通过Navicat可以连接到postgresql数据库：

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard-1625492317572.png)



#### 2.1.2 安装kong

centos7下安装kong:  

https://download.konghq.com/gateway-1.x-centos-7/Packages/k/

##### 安装命令

```shell
wget https://download.konghq.com/gateway-1.x-centos-7/Packages/k/kong-1.5.1.el7.amd64.rpm
sudo yum install kong-1.5.1.el7.amd64.rpm 
```

##### 配置kong

Kong 的默认配置文件是 /etc/kong/kong.conf.default，使用 cp /etc/kong/kong.conf.default /etc/kong/kong.conf 命令，复制一份新的配置文件。

复制完成后，修改 /etc/kong/kong.conf 配置文件，设置使用 PostgreSQL 数据库。

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard-1625492540794.png)

执行 kong migrations bootstrap -c /etc/kong/kong.conf 命令，进行 Kong 的 PostgreSQL 数据库的表初始化。

navicat中可以看到表信息

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard-1625492565178.png)

执行 kong start -c /etc/kong/kong.conf 命令，执行 Kong 的启动。

```shell
#启动命令
kong start -c /etc/kong/kong.conf 
# 停止命令
kong stop
# 重新加载kong
kong reload
```

启动成功时，会看到 Kong started 日志。

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/clipboard-1625493067207.png)

默认情况下，Kong 绑定 4 个端口：

- Proxy 8000：接收客户端的 HTTP 请求，并转发到后端的 Upstream。
- Proxy 8443：接收客户端的 HTTPS 请求，并转发到后端的 Upstream。
- Admin 8001：接收管理员的 HTTP 请求，进行 Kong 的管理。
- Admin 8444：接收管理员的 HTTPS 请求，进行 Kong 的管理。

```shell
# 请求 Proxy 端口
$ curl http://127.0.0.1:8000
{"message":"no Route matched with those values"} 
# 因为我们暂时没配置 Kong 路由。

# 请求 Admin 端口
# 注意，考虑到安全性，Admin 端口只允许本机访问。
$ curl http://127.0.0.1:8001
{"plugins":{"enabled_in_cluster":[],"available_on_server":{... // 省略 
```

### 2.2 基于docker搭建

前提：准备好docker环境

![image-20210706173841513](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706173841513.png)

Kong 安装有两种方式一种是没有数据库依赖的DB-less 模式，另一种是with a Database 模式。我们这里使用第二种带Database的模式，因为这种模式功能更全。

#### 2.2.1 docker安装Kong

##### 构建Kong的容器网络

首先我们创建一个Docker自定义网络，以允许容器相互发现和通信。在下面的创建命令中`kong-net`是我们创建的Docker网络名称，当然你可以使用你认为合适的名称。

```shell
 docker network create kong-net
```

##### 搭建数据库环境

Kong 目前使用Cassandra(Facebook开源的分布式的NoSQL数据库) 或者PostgreSql,你可以执行以下命令中的一个来选择你的Database。请注意定义网络 `--network=kong-net` 。

- Cassandra容器：

```shell
docker run -d --name kong-database \
           --network=kong-net \
           -p 9042:9042 \
           cassandra:3
```

- PostgreSQL容器：

  ```shell
  docker run -d --name kong-database \
             --network=kong-net \
             -p 5432:5432 \
             -e "POSTGRES_USER=kong" \
             -e "POSTGRES_DB=kong" \
             postgres:9.6
  ```

这里有个小问题。如果你使用的是PostgreSQL，想挂载卷持久化数据到宿主机。通过 `-v` 命令是不好用的。这里推荐你使用 `docker volume create` 命令来创建一个挂载。

```shell
docker volume create kong-volume
```

然后上面的PostgreSQL就可以通过` - v kong-volume:/var/lib/postgresql/data` 进行挂载了。

```shell
docker run -d --name kong-database \
           --network=kong-net \
           -p 5432:5432 \
           -v kong-volume:/var/lib/postgresql/data \
           -e "POSTGRES_USER=kong" \
           -e "POSTGRES_DB=kong" \
           -e "POSTGRES_PASSWORD=kong"  \
           postgres:9.6
```

##### 初始化或者迁移数据库

我们使用`docker run --rm`来初始化数据库，该命令执行后会退出容器而保留内部的数据卷（volume）。

```shell
docker run --rm \
 --network=kong-net \
 -e "KONG_DATABASE=postgres" \
 -e "KONG_PG_HOST=kong-database" \
 -e "KONG_PG_PASSWORD=kong" \
 -e "KONG_CASSANDRA_CONTACT_POINTS=kong-database" \
 kong:latest kong migrations bootstrap
```

navicat中可以看到表信息

![image-20210706180519114](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706180519114.png)

##### 启动Kong容器

完成初始化或者迁移数据库后，我们就可以启动一个连接到数据库容器的Kong容器，请务必保证你的数据库容器启动状态，同时检查所有的环境参数 `-e` 是否是你定义的环境。

```shell
docker run -d --name kong \
 --network=kong-net \
 -e "KONG_DATABASE=postgres" \
 -e "KONG_PG_HOST=kong-database" \
 -e "KONG_PG_PASSWORD=kong" \
 -e "KONG_CASSANDRA_CONTACT_POINTS=kong-database" \
 -e "KONG_PROXY_ACCESS_LOG=/dev/stdout" \
 -e "KONG_ADMIN_ACCESS_LOG=/dev/stdout" \
 -e "KONG_PROXY_ERROR_LOG=/dev/stderr" \
 -e "KONG_ADMIN_ERROR_LOG=/dev/stderr" \
 -e "KONG_ADMIN_LISTEN=0.0.0.0:8001, 0.0.0.0:8444 ssl" \
 -p 8000:8000 \
 -p 8443:8443 \
 -p 8001:8001 \
 -p 8444:8444 \
 kong:latest
```

##### 验证

可通过 `curl -i http://192.168.65.200:8001/` 或者浏览器调用 http://192.168.65.200:8001/ 来验证Kong Admin 是否联通 。

![image-20210706180124189](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706180124189.png)



### 2.3 安装Kong 管理UI

Kong 企业版提供了管理UI，开源版本是没有的。但是有很多的开源的管理 UI ，其中比较好用的是Konga。项目地址：https://github.com/pantsel/konga

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/H5df6702d77044208ab6672291be030fbW.png)

Konga 主要是用 AngularJS 写的，运行于nodejs服务端。具有以下特性：

- 管理所有Kong Admin API对象。
- 支持从远程源（数据库，文件，API等）导入使用者。
- 管理多个Kong节点。使用快照备份，还原和迁移Kong节点。
- 使用运行状况检查监视节点和API状态。
- 支持电子邮件和闲置通知。
- 支持多用户。
- 易于数据库集成（MySQL，postgresSQL，MongoDB，SQL Server）。



#### 2.3.1 docker安装Konga

##### 启动Konga数据库容器

Konga支持PostgreSQL数据库。定义挂载卷`konga-postgresql` 

```shell
docker volume create konga-postgresql
```

```shell
 docker run -d --name konga-database  \
	 --network=kong-net  \
                    -p 5433:5432 \
                    -v  konga-postgresql:/var/lib/postgresql/data  \
                    -e "POSTGRES_USER=konga"  \
                    -e "POSTGRES_DB=konga" \
                    -e "POSTGRES_PASSWORD=konga"  \
                    postgres:9.6
```

![image-20210706171357121](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706171357121.png)

##### 初始化 PostgreSQL 数据库

```
docker run --rm  --network=kong-net  \
                       pantsel/konga:latest -c prepare -a postgres -u postgres://konga:konga@konga-database:5432/konga
```

相关命令解读：

| 命令 | 描述                                    | 默认 |
| :--- | :-------------------------------------- | :--- |
| -c   | 执行的命令，这里我们执行的是prepare     | -    |
| -a   | adapter 简写 ，可以是postgres 或者mysql | -    |
| -u   | db url 数据库连接全称                   | -    |

![image-20210706171307679](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706171307679.png)

到此Konga的数据库环境就搞定了，通过Navicat可以查看到konga数据库及其数据表。

![image-20210706172207929](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706172207929.png)

![image-20210706172228315](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706172228315.png)



##### 环境参数

Konga 还有一些可配置的环境参数：

![img](https://raw.githubusercontent.com/zpnvliba/images/main/kong/H68798d431eba4fc6a70d160ca3929ffdF.png)

##### 启动Konga

通过以下命令就可以启动Konga容器了

```
docker run -d -p 1337:1337  \
               --network kong-net  \
               -e "DB_ADAPTER=postgres"  \
               -e "DB_URI=postgres://konga:konga@konga-database:5432/konga"  \
               -e "NODE_ENV=production"  \
               -e "DB_PASSWORD=konga" \
               --name konga \
               pantsel/konga
```

运行完后，如果成功可以通过http://192.168.65.200:1337/ 链接到控制台。

![image-20210706172345755](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706172345755.png)

通过注册后进入，然后在dashboard面板里面添加Kong的管理Api路径 `http://ip:8001`

![image-20210706180801017](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706180801017.png)

![image-20210706180945908](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706180945908.png)

![image-20210706181012095](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210706181012095.png)



## 3. Kong快速开始

### 3.1 动态负载均衡实现

nginx下负载均衡配置

```
upstream tulingmall-product-upstream {
	server 192.168.65.190:8866 weight=100;
	server 192.168.65.190:8867 weight=100;
}

server {
	listen	80;
	location /pms/ {
		proxy_pass http://tulingmall-product-upstream;
	}
}
```

通过 **Kong Admin API** 进行上述的负载均衡的配置

https://docs.konghq.com/enterprise/2.4.x/admin-api/

| Kong 组件    | 说明                                                         |
| :----------- | :----------------------------------------------------------- |
| **service**  | service 对应服务，可以直接指向一个 API 服务节点(`host` 参数设置为 ip + port)，也可以指定一个 upstream 实现负载均衡。简单来说，服务用于映射被转发的后端 API 的节点集合 |
| **route**    | route 对应路由，它负责匹配实际的请求，映射到 **service** 中  |
| **upstream** | upstream 对应一**组** API 节点，实现负载均衡                 |
| **target**   | target 对应一**个** API 节点                                 |

![image-20210708205407817](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210708205407817.png)

####  创建 upstream 和 target

调用 Kong Admin API `/upstreams`，创建名字为 `demo-upstream` 的 **upstream**

```http
$ curl -X POST http://127.0.0.1:8001/upstreams --data "name=tulingmall-product-upstream"
```

![image-20210709094648121](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709094648121.png)

 调用 Kong Admin API `/upstreams/{upstream}/targets`，创建 tulingmall-product服务对应的 2 个 **target**。注意，`{upstream}` 路径参数为 upstream 的名字。

```http
# 192.168.65.190:8866 对应的 target
$ curl -X POST http://127.0.0.1:8001/upstreams/tulingmall-product-upstream/targets --data "target=192.168.65.190:8866" --data "weight=100"
# 192.168.65.190:8867 对应的 target
$ curl -X POST http://127.0.0.1:8001/upstreams/tulingmall-product-upstream/targets --data "target=192.168.65.190:8867" --data "weight=100"

```



![image-20210709095041262](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709095041262.png)



#### 创建 service 和 route

调用 Kong Admin API `/services`，创建名字为 `tulingmall-product` 的 **service**。host 参数，用于设置对应的 upstream 的名字。

```http
curl -X POST http://127.0.0.1:8001/services --data "name=tulingmall-product" --data "host=tulingmall-product-upstream" --data "path=/pms"
```

![image-20210709095602955](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709095602955.png)

调用 Kong Admin API `services/${service}/routes`，创建一个请求路径为 `path` 的 **route**。注意，`{service}` 路径参数，为 service的名字。

```http
curl -X POST http://localhost:8001/services/tulingmall-product/routes --data "name=tulingmall-product-route" --data "paths[]=/pms"
```

![image-20210709110259411](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709110259411.png)

#### 测试

```http
curl http://127.0.0.1:8000/pms/productInfo/42
```



### 3.2 kong限流配置

Kong 提供了 [Rate Limiting](https://docs.konghq.com/hub/kong-inc/rate-limiting) 插件，实现对请求的**限流**功能，避免过大的请求量过大，将后端服务打挂。

Rate Limiting 支持秒/分/小时/日/月/年多种**时间维度**的限流，并且可以组合使用。例如说：限制每秒最多 100 次请求，并且每分钟最多 1000 次请求。

Rate Limiting 支持 `consumer`、`credential`、`ip` 三种**基础维度**的限流，默认为 `consumer`。例如说：设置每个 IP 允许每秒请求的次数。计数的存储，支持使用 `local`、`cluster`、`redis` 三种方式进行存储，默认为 `cluster`：

- `local`：存储在 Nginx 本地，实现单实例限流。
- `cluster`：存储在 Cassandra 或 PostgreSQL 数据库，实现集群限流。
- `redis`：存储在 Redis 数据库，实现集群限流。

Rate Limiting 采用的限流算法是**计数器**的方式，所以无法提供类似令牌桶算法的平滑限流能力。

#### 配置 Rate Limiting 插件

调用 Kong Admin API `services/${service}/plugins`，创建 Rate Limiting 插件的配置：

```shell
# 服务上启用插件
$ curl -X POST http://127.0.0.1:8001/services/tulingmall-product/plugins \
    --data "name=rate-limiting"  \
    --data "config.second=1" \
    --data "config.limit_by=ip"
    
# 路由上启用插件
$ curl -X POST http://127.0.0.1:8001/routes/{route_id}/plugins \
    --data "name=rate-limiting"  \
    --data "config.second=5" \
    --data "config.hour=10000"

# consumer上启用插件
$ curl -X POST http://127.0.0.1:8001/plugins \
    --data "name=rate-limiting" \
    --data "consumer_id={consumer_id}"  \
    --data "config.second=5" \
    --data "config.hour=10000"

    
```

- `name` 参数，设置为 `rate-limiting` 表示使用 Rate Limiting 插件。

- `config.second` 参数，设置为 1 表示每秒允许 1 次请求。

- `config.limit_by` 参数，设置为 `ip` 表示使用 IP 基础维度的限流。

  也可以通过konga UI操作添加rate-limiting插件

![image-20210709113025416](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709113025416.png)

#### 测试

请求超过阈值，会被kong限流

![image-20210709113115680](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709113115680.png)

### 3.3 Basic Auth身份认证

#### 配置Basic Auth插件

```shell
# 在服务上配置插件
curl -X POST http://127.0.0.1:8001/services/{service}/plugins \
    --data "name=basic-auth"  \
    --data "config.hide_credentials=true"

#在路由上配置插件
curl -X POST http://127.0.0.1:8001/routes/{route_id}/plugins \
    --data "name=basic-auth"  \
    --data "config.hide_credentials=true"

```

通过konga UI为路由添加basic-auth插件

![image-20210709131412984](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709131412984.png)

创建用户并添加Basic凭证

![image-20210709132201771](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709132201771.png)

#### 测试

![image-20210709132404181](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709132404181.png)





### 3.4 JWT身份认证

#### 配置 JWT 插件

调用 Kong Admin API `services/${service}/plugins`，创建 JWT 插件的配置：

```
curl -X POST http://127.0.0.1:8001/services/tulingmall-product/plugins \
    --data "name=jwt"
```

- `name` 参数，设置为 `jwt` 表示使用 JWT 插件。

```shell
# 查看插件列表
curl -X GET localhost:8001/services/tulingmall-product/plugins

#查看jwt插件
curl -X GET localhost:8001/services/tulingmall-product/plugins/jwt

#删除jwt插件
curl -X DELETE localhost:8001/services/tulingmall-product/plugins/{jwt.id}
```

通过konga UI操作添加`jwt` 插件

![image-20210709113600895](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709113600895.png)

#### 测试

请求被kong安全拦截

![image-20210709113710269](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709113710269.png)

#### 创建Consumer

调用 Kong Admin API `consumers`，创建一个 Consumer 消费者：

```
$ curl -i -X POST http://localhost:8001/consumers/ \
    --data "username=fox"
```

![image-20210709113901936](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709113901936.png)

#### 创建 consumer 的 jwt 凭证

调用 Kong Admin API `consumers/{username}/{plugin}`，**生成**该消费者的 JWT 信息：

- `{username}` 路径参数，为 Consumer 的用户名。
- `{plugin}` 路径参数，为 Plugin 的插件名。

可以指定算法`algorithm`，`iss`签发者`key`，密钥`secret`，也可以省略，会自动生成。

```shell
$ curl -i -X POST http://localhost:8001/consumers/fox/jwt/ \
-d "algorithm=HS256" \
-d "key=fox123" \
-d "secret=uFLMFeKPPL525ppKrqmUiT2rlvkpLc9u"

```

![image-20210709115927204](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709115927204.png)

```josn
{
    "rsa_public_key":null,
    "algorithm":"HS256",
    "id":"3dc4d177-8a7a-4edc-bc88-ee7aa2447fc7",
    "tags":null,
    "consumer":{
        "id":"8e7fb82d-68ef-4f2b-a30c-613866378525"
    },
    "secret":"uFLMFeKPPL525ppKrqmUiT2rlvkpLc9u",
    "created_at":1625803149,
    "key":"fox123"
}
```

![image-20210709120408466](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709120408466.png)

查看fox的jwt凭证

```
curl -X GET localhost:8001/consumers/fox/jwt
```

![image-20210709120215620](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709120215620.png)

#### 生成jwt token

业务服务器根据`kong`生成的`jwt`凭证中的`algorithm、key（iss）、secret`进行`token`的演算和下发。请求`鉴权接口`需携带
`Authorization: Bearer jwt`进行请求。测试可以在https://jwt.io/中通过Debugger生成jwt token

![image-20210709120941247](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709120941247.png)

获取到jwt token令牌：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJpc3MiOiJmb3gxMjMifQ.hqHGVujYheALxXpEVtgisA5pPTGfQYet0IKadnYPtj8
```

#### 测试

```
curl http://192.168.65.200:8000/pms/productInfo/42 \
    -H "Authorization: Bearer  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJpc3MiOiJmb3gxMjMifQ.hqHGVujYheALxXpEVtgisA5pPTGfQYet0IKadnYPtj8"

```

![image-20210709130109340](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709130109340.png)



### 3.5 黑白名单配置

#### 配置插件

```shell
# 在服务上启用插件
$ curl -X POST http://kong:8001/services/{service}/plugins \
    --data "name=ip-restriction"  \
    --data "config.whitelist=54.13.21.1, 143.1.0.0/24"

# 在路由上启用插件
$ curl -X POST http://kong:8001/routes/{route_id}/plugins \
    --data "name=ip-restriction"  \
    --data "config.whitelist=54.13.21.1, 143.1.0.0/24"

```

- config.whitelist ：白名单，逗号分隔的IPs或CIDR范围。
-  config.blacklist ：白名单，逗号分隔的IPs或CIDR范围。

```xshell
curl -X POST http://127.0.0.1:8001/routes/ad515a07-bae4-4b54-a927-35bc6c85565b/plugins \
    --data "name=ip-restriction"  \
    --data "config.whitelist=192.168.65.200"
```

#### 测试

当前本机器IP地址为:   192.168.65.103

![image-20210709135247424](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709135247424.png)

将本机ip加入到白名单

![image-20210709135438312](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709135438312.png)

![image-20210709135449252](https://raw.githubusercontent.com/zpnvliba/images/main/kong/image-20210709135449252.png)