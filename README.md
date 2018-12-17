# kuber-maas

1. Figure out how to deploy/maintain a Kubernetes cluster in a MAAS infrastructure. We know that the conjure-up tool-chain provides an easy way to achieve that, although it's probably too large for the anticipated use-case. A first iteration could wrap conjure-up  to transparently deploy Kubernetes (those deploys can be automated with the use of Conjurefiles). Focus in writing a pluggable code, in case conjure-up needs to be replaced by another deployment tool. Find a desirable configuration for Kubernetes for automated deployment in MAAS. 

→ first conjure-up needs to be installed on the local machine. If you don't have 'snap' installed on your system yet, make sure to install it:

```sh
$ sudo apt update
$ sudo apt install snapd
```
Afterwards, conjure-up should be installed with snap:

```sh
$ sudo snap install conjure-up --classic
```

Additional information can be found on the website:
https://docs.conjure-up.io/stable/en/user-manual#installing-conjure-up

We will also need the Kubernetes command-line tool. In order to install it with snap run the following command:

```sh
$  sudo snap install kubectl --classic
```

Verify the installation with 

```sh
$  kubectl version
```

pull the git repo in a directory:

https://github.com/alexakarp/kuber_maas
open a terminal in the directory, execute the following commands to run the script

```sh
$  virtualenv venv
$  . venv/bin/activate
$  pip install -r requirements.txt
$  python app.py
```

The Console output should be something like this:
> Serving Flask app "app" (lazy loading)
> Environment: production
> WARNING: Do not use the development server in a production environment.
> Use a production WSGI server instead.
> Debug mode: on
> Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
> Restarting with stat
> No cluster detected. Please deploy a cluster first using the endpoint /maas/
>  Debugger is active!
>  Debugger PIN: 119-668-834


Now try to deploy the cluster with a POST request

curl -X POST \ 'http://127.0.0.1:5000/maas/?maas_endpoint=localhost&api_key=apikey123%21%21&operation=create'

The app checks, if there is a cluster deployed already. The deployment locally can take 17-20 minutes! After succesful deployment it will output the cluster status and:
> Installation of your big software is now complete

2. Build a REST service that exposes an endpoint through which is possible to deploy/destroy a Kubernetes cluster in a MAAS pool. The service must know how many clusters it has deployed and how many are currently active, and must be able to access and deploy applications on these clusters. The first iteration could consider that there is either one or zero clusters deployed at any given time.


3. Create an endpoint in the aforementioned REST service for deploying applications on top of the Kubernetes cluster. An initial iteration could deploy a simple container with a “hello-world” program.


4. Modify the service to include a container building pipeline, making it possible for the user to just provide an application binary and a few specifications. The service would then wrap the binary in a Docker image and build it, then deploying it on top of the Kubernetes cluster.
