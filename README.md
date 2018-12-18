# kuber-maas
# Installation
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


# Using the service

There are two API endpoints:
### 1. the endpoint for the high-level cluster operation
http://127.0.0.1:5000/maas/

Two operations are possible on the maas endpoint:
#### GET operation for checking if the cluster is already deployed

```sh
curl -X GET http://127.0.0.1:5000/maas/
```
The response will either be
> "Cluster already running, no need to conjure-up"
or
> "Cluster not running"

#### POST operation to deploy the kubernetes cluster
```sh
curl -X POST \
  'http://127.0.0.1:5000/maas/?maas_endpoint=localhost&api_key=apikey123%21%21&operation=create'
```
**maas_endpoint** {string} - specifies, where the cluster should be deployed to. Could be a maas instance or localhost
**api_key** {string} - can be used to verify user credentials of maas [not implemented yet]
**operation** {string} - 'create' to deploy a cluster via conjure-up, 'destroy' to conjure-down the cluster [TODO: automate conjure-down]

The service will create a local Conjurefile according to the input data and run conjure-up.
**WARNING: the deployment of the cluster can take a long time (17-20 minutes)! Don't interrupt it before, otherwise it might corrupt the deployment**

After succesful deployment it will output the cluster status and:

> Installation of your big software is now complete


### 2. the enpoint for the applications on the cluster:
http://127.0.0.1:5000/apps/
#### GET Operation to show deployments saved during runtime of the service

```sh
curl -X GET http://127.0.0.1:5000/apps/
```
The Response could look like this:

```json
{
    "37d3ecde-02d2-11e9-a821-f2e4555daa4e": {
        "deployment_name": "nginx",
        "replicas": 3,
        "expose": true,
        "service": {
            "name": "nginx",
            "cluster_ip": "10.152.183.89",
            "node_port": 30284,
            "port": 8080
        }
    },
    "95409701-02d2-11e9-a821-f2e4555daa4e": {
        "deployment_name": "nginx23",
        "replicas": 4,
        "expose": false,
        "service": {}
    }
}
```

Notice that the deployment 'nginx' has an associated service running, while 'nginx23' is deployed without a service.

#### POST operation to create a new deployment on the cluster with or without a service to expose it

```sh
curl -X POST \
  'http://127.0.0.1:5000/apps/?replicas=4&expose=true&port=8080&name=nginx&image=nginx'
```
**replicas** {int} - specifies the number of replicas on the cluster
**expose** {true/false} - if true creates a service for the deployment
**port** {int} - can specify the port
**name** {string} - name of the deployment
**image** {string} - name of the image to be deployed

The response will for example say 'created: nginx'. Every created deployment will be saved in a dictionary with its associated UID and possible service.


#### DELETE operation to delete a deployment with a possibly associated service, either by UID or manually by name
###### Deleting a service that was created during runtime of the service by UID:
```sh
curl -X DELETE \
  'http://127.0.0.1:5000/apps/?uid=37d3ecde-02d2-11e9-a821-f2ecurl -X DELETE \
  'http://127.0.0.1:5000/apps/?service=false&name=nginx23'
The response will be the status of the deletion, for example:
```json
{'observedGeneration': 1, 'replicas': 4, 'updatedReplicas': 4, 'readyReplicas': 4, 'availableReplicas': 4, 'conditions': [{'type': 'Available', 'status': 'True', 'lastUpdateTime': '2018-12-18T15:53:57Z', 'lastTransitionTime': '2018-12-18T15:53:57Z', 'reason': 'MinimumReplicasAvailable', 'message': 'Deployment has minimum availability.'}]}
```
This will also remove the entry from the dictionary of deployments

###### Deleting a service manually with name:
If a deployment exists without being created in this service's runtime, it will not be included in the dictionary. In that case, it can be deleted manually
```sh
curl -X DELETE \
  'http://127.0.0.1:5000/apps/?service=false&name=nginx23'
```
**service** {true/false} - indicates whether an associated service is to be deleted aswell
**name** {string} - name of the deployment that is to be deleted

The response will look similar to the one with UID.



