$Env:KUBECONFIG = "C:\Users\pklyu\Desktop\git\kubertest\facesegm\timeweb\config.yaml"\
docker build -t face-detection-app:latest .

docker tag face-detection-app:latest pklyuchko/face-detection-app:latest
docker push pklyuchko/face-detection-app:latest

rem docker run -d --name face-detection-container -p 8000:8000 face-detection-app



