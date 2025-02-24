An (experimental) template to create a scala job which uploads an assembly jar to your Databricks workspace using scala dbconnect. This can also be reused for local development with dbconnect serverless

Run 
```
mkdir dabs_test && cd dabs_test && databricks bundle init --template-dir contrib/templates/scala-job https://github.com/databricks/bundle-examples
```

and follow the generated README.md to get started.