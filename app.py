import sys
import os
from flask import Flask
from flask_restful import Api, Resource, reqparse
from kubernetes import client, config, watch
from io import StringIO
import yaml
import os.path
from pathlib import Path
from os.path import expanduser



app = Flask(__name__)
api = Api(app)

#some global variables to make it pluggable --> can be more parameterized
deployment_operator_deploy = 'conjure-up'
deployment_operator_teardown = 'conjure-down'
controller = 'localhost-localhost'
extensions_v1beta1 = client.ExtensionsV1beta1Api()
DEPLOYMENT_NAME = "nginx-deployment"
config.load_kube_config()
services = {}


class maas(Resource):
    def get(self):
        if check_cluster():
            return ('Cluster already running, no need to conjure-up'), 200
        return ('Cluster not running'), 404

    def post(self):
        if check_cluster():
            return 'Cluster already running, no need to conjure-up', 409
        parser = reqparse.RequestParser()
        parser.add_argument('maas_endpoint')
        parser.add_argument('api_key')
        parser.add_argument('operation')
        args = parser.parse_args()

        maas_endpoint = args["maas_endpoint"]
        api_key = args["api_key"]

        output = "Running Conjure-Up with: \n" + "MaaS Endpoint: " + maas_endpoint + "\n" + "API_Key: " + api_key

        #Creating Conjurefile
        f = open('Conjurefile', 'w+')
        f.write("# Core Spell\n")
        f.write("spell: canonical-kubernetes\n\n")
        f.write("cloud: " + maas_endpoint + "\n\n")
        f.write("controller: " + controller + "\n\n")
        f.write("debug: true")
        f.flush()

        #Executing conjure-up via terminal --> takes a LONG time!
        if(args["operation"] == 'create'):
            #os.system('juju bootstrap - -bootstrap - series = xenial')
            os.system(deployment_operator_deploy)

        if (args["operation"] == 'destroy'):
            os.system(deployment_operator_teardown)

        return output, 200

class apps(Resource):
    def get(self):
        #config.load_kube_config()

        print(services)
        v1 = client.CoreV1Api()
        #print("Listing pods with their IPs: ")
        #bufferstring = ''
        #just returning pods with their IPs as a check that they are up
        #ret = v1.list_pod_for_all_namespaces(watch=False)

        #for i in ret.items:
        #    bufferstring = bufferstring + i.status.pod_ip + " " + i.metadata.namespace + " " + i.metadata.name + " ### "

        return str(services), 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('replicas')
        parser.add_argument('expose')
        parser.add_argument('port')
        parser.add_argument('name')
        parser.add_argument('image')
        args = parser.parse_args()
        port_nr = int(args['port'])
        replicas = int(args['replicas'])
        name = args['name']
        image = args['image']

        if not check_cluster():
            return 'Please create cluster first with POST to /maas/ endpoint', 500

        if name == '' or name == None:
            return 'Please specify the app you want to depploy with \'appname\' ', 500;

        if image == '' or image == None:
            return 'Please specify the image you want to depploy with \'image\' ', 500;


        extensions_v1beta1 = client.ExtensionsV1beta1Api()
        deployment = create_deployment_object(name, image, replicas)
        test = create_deployment(extensions_v1beta1, deployment)
        api_instance = client.CoreV1Api()


        #if user wants it exposed, service will be created
        if(args['expose'] == 'true'):
            service = client.V1Service()
            # specifying service parameters (can be more parameterized)
            service.api_version = "v1"
            service.kind = "Service"
            service.metadata = client.V1ObjectMeta(name=name)
            spec = client.V1ServiceSpec()
            spec.selector = {"app": name}
            spec.type = "NodePort"
            spec.ports = [client.V1ServicePort(protocol="TCP", port=port_nr)]
            service.spec = spec
            api_instance.create_namespaced_service(namespace="default", body=service)
            service_instance = name + '1234'
            services[service_instance] = service
            return ('created: ' + name), 200


        return ('created: ' + name), 200

    def delete(self):

        parser = reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('service')
        args = parser.parse_args()
        name = args['name']
        service = args['service']
        extensions_v1beta1 = client.ExtensionsV1beta1Api()

        if service == 'true':
            api_instance = client.CoreV1Api()
            # deleting of service not yet working
            api_instance.delete_namespaced_service(name='nginx', namespace="default")



        #delete deployment
        response_msg = delete_deployment(extensions_v1beta1, name)
        testoutput = str(response_msg.status)
        return testoutput, 200


def create_deployment_object(name, image, replicas):
    # Configureate Pod template container
    container = client.V1Container(
        name=name,
        image=image,
        ports=[client.V1ContainerPort(container_port=80)])
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": name}),
        spec=client.V1PodSpec(containers=[container]))
    # Create the specification of deployment
    spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=replicas,
        template=template)
    # Instantiate the deployment object
    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=name),
        spec=spec)

    return deployment


def create_deployment(api_instance, deployment):
    # Create deployement
    api_response = api_instance.create_namespaced_deployment(
        body=deployment,
        namespace="default")
    print("Deployment created. status='%s'" % str(api_response.status))

    return api_response


def delete_deployment(api_instance, name):
    # Delete deployment
    api_response = api_instance.delete_namespaced_deployment(
        name=name,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5))
    print("Deployment deleted. status='%s'" % str(api_response.status))
    return api_response


def check_cluster():
    home = expanduser("~")
    filename = home + '/.kube/config'
    my_file = Path(filename)
    if my_file.is_file():
        print('Cluster is already there!')
        return True
    else:
        print('No cluster detected. Please deploy a cluster first using the endpoint /maas/')
        return False


def main():
    api.add_resource(maas, "/maas/")
    api.add_resource(apps, "/apps/")




    check_cluster()
    app.run(debug=True)


if __name__ == '__main__':
    main()





