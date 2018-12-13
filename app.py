import sys
import os
from flask import Flask
from flask_restful import Api, Resource, reqparse
from kubernetes import client, config, watch
from io import StringIO
import yaml

app = Flask(__name__)
api = Api(app)

#some global variables to make it pluggable --> can be more parameterized
deployment_operator_deploy = 'conjure-up'
deployment_operator_teardown = 'conjure-down'
controller = 'localhost-localhost'
extensions_v1beta1 = client.ExtensionsV1beta1Api()
config.load_kube_config()
DEPLOYMENT_NAME = "nginx-deployment"


class maas(Resource):
    def get(self):
        return ('Cluster Running Message'), 404

    def post(self):
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
        config.load_kube_config()
        v1 = client.CoreV1Api()
        print("Listing pods with their IPs: ")
        bufferstring = ''
        #just returning pods with their IPs as a check that they are up
        ret = v1.list_pod_for_all_namespaces(watch=False)

        for i in ret.items:
            bufferstring = bufferstring + i.status.pod_ip + " " + i.metadata.namespace + " " + i.metadata.name + " ### "

        return bufferstring, 404

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('nr_nodes')
        parser.add_argument('expose')
        parser.add_argument('port')
        args = parser.parse_args()
        port_nr = int(args['port'])
        nodes_nr = int(args['nr_nodes'])

        api_instance = client.CoreV1Api()
        service = client.V1Service()
        #specifying service parameters (can be more parameterized)
        service.api_version = "v1"
        service.kind = "Service"
        service.metadata = client.V1ObjectMeta(name=DEPLOYMENT_NAME)
        spec = client.V1ServiceSpec()
        spec.selector = {"app": "MyApp"}
        spec.type = "NodePort"
        spec.ports = [client.V1ServicePort(protocol="TCP", port=port_nr)]
        service.spec = spec

        extensions_v1beta1 = client.ExtensionsV1beta1Api()
        deployment = create_deployment_object(nodes_nr)
        create_deployment(extensions_v1beta1, deployment)

        #if user wants it exposed, service will be created
        if(args['expose'] == 'true'):
            api_instance.create_namespaced_service(namespace="default", body=service)
        return ('created :')

    def delete(self):
        api_instance = client.CoreV1Api()
        extensions_v1beta1 = client.ExtensionsV1beta1Api()

        #deleting of service not yet working
        #api_instance.delete_namespaced_service(name=DEPLOYMENT_NAME, namespace="default")

        #delete deployment
        delete_deployment(extensions_v1beta1)
        return ('deleted')


def create_deployment_object(nr_nodes):
    # Configureate Pod template container
    container = client.V1Container(
        name="nginx",
        image="nginx:1.7.9",
        ports=[client.V1ContainerPort(container_port=80)])
    # Create and configurate a spec section
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "nginx"}),
        spec=client.V1PodSpec(containers=[container]))
    # Create the specification of deployment
    spec = client.ExtensionsV1beta1DeploymentSpec(
        replicas=nr_nodes,
        template=template)
    # Instantiate the deployment object
    deployment = client.ExtensionsV1beta1Deployment(
        api_version="extensions/v1beta1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=DEPLOYMENT_NAME),
        spec=spec)

    return deployment


def create_deployment(api_instance, deployment):
    # Create deployement
    api_response = api_instance.create_namespaced_deployment(
        body=deployment,
        namespace="default")
    print("Deployment created. status='%s'" % str(api_response.status))


def update_deployment(api_instance, deployment):
    # Update container image
    deployment.spec.template.spec.containers[0].image = "nginx:1.9.1"
    # Update the deployment
    api_response = api_instance.patch_namespaced_deployment(
        name=DEPLOYMENT_NAME,
        namespace="default",
        body=deployment)
    print("Deployment updated. status='%s'" % str(api_response.status))


def delete_deployment(api_instance):
    # Delete deployment
    api_response = api_instance.delete_namespaced_deployment(
        name=DEPLOYMENT_NAME,
        namespace="default",
        body=client.V1DeleteOptions(
            propagation_policy='Foreground',
            grace_period_seconds=5))
    print("Deployment deleted. status='%s'" % str(api_response.status))


def main():
    api.add_resource(maas, "/maas/")
    api.add_resource(apps, "/apps/")
    app.run(debug=True)


if __name__ == '__main__':
    main()





