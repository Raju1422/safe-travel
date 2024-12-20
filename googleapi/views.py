import requests
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import AddressSerializer
import numpy as np
from sklearn.cluster import KMeans
import json

class CoordinatesView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddressSerializer(data=request.data)
        
        if serializer.is_valid():
            source_address = serializer.validated_data['source']
            destination_address = serializer.validated_data['destination']

            url = 'https://nominatim.openstreetmap.org/search'

            def get_lat_lng(address):
                params = {
                    'q': address,
                    'format': 'json',
                    'addressdetails': 1
                }
                headers = {
                    'User-Agent': 'YourAppName'
                }
                response = requests.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if data:
                            return data[0]['lat'], data[0]['lon']
                    except ValueError:
                        return None, None
                return None, None

            source_lat, source_lng = get_lat_lng(source_address)
            destination_lat, destination_lng = get_lat_lng(destination_address)

            if source_lat is None or destination_lat is None:
                return Response({'error': 'Address not found or invalid address'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'source': {'latitude': source_lat, 'longitude': source_lng},
                'destination': {'latitude': destination_lat, 'longitude': destination_lng}
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


# To get the paths

class MultiPathRiskView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            source_address = serializer.validated_data['source']
            destination_address = serializer.validated_data['destination']

            url = 'https://nominatim.openstreetmap.org/search'

            # Fetch latitude and longitude
            def get_lat_lng(address):
                try:
                    params = {'q': address, 'format': 'json', 'addressdetails': 1}
                    headers = {'User-Agent': 'YourAppName'}
                    response = requests.get(url, params=params, headers=headers)
                    response.raise_for_status()  # Raise exception for HTTP errors
                    data = response.json()
                    if data and len(data) > 0:
                        return float(data[0].get('lat', 0)), float(data[0].get('lon', 0))
                except Exception as e:
                    logger.error(f"Error fetching coordinates for {address}: {e}")
                    return None, None

            source_coords = get_lat_lng(source_address)
            destination_coords = get_lat_lng(destination_address)

            if not source_coords or not destination_coords:
                return Response(
                    {'error': 'Invalid source or destination address'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate multiple paths
            def generate_multiple_paths(source, destination, num_paths=5, steps=10):
                paths = []
                for i in range(num_paths):
                    intermediate_path = []
                    for step in range(steps):
                        fraction = min(1, max(0, (step + i * 0.1) / steps))
                        intermediate_lat = source[0] + fraction * (destination[0] - source[0])
                        intermediate_lng = source[1] + fraction * (destination[1] - source[1])
                        intermediate_path.append([intermediate_lat, intermediate_lng])
                    paths.append(intermediate_path)
                return paths

            paths = generate_multiple_paths(source_coords, destination_coords)

            # Load the model
            try:
                with open('googleapi/model.json', 'r') as model_file:
                    model_data = json.load(model_file)
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logger.error(f"Error loading model.json: {e}")
                return Response(
                    {'error': 'Failed to load classification model'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Classify paths
            def classify_paths(model, paths):
                try:
                    feature_vectors = [np.mean(path, axis=0).tolist() for path in paths]
                    kmeans = KMeans(n_clusters=3, random_state=42)
                    kmeans.cluster_centers_ = np.array(model['centroids'])
                    labels = kmeans.fit_predict(feature_vectors)  # Refit the model
                    risk_mapping = {0: "High Risk", 1: "Low Risk", 2: "Safe"}
                    return [{"path": path, "risk": risk_mapping[label]} for path, label in zip(paths, labels)]
                except Exception as e:
                    logger.error(f"Error in path classification: {e}")
                    raise

            try:
                classified_paths = classify_paths(model_data, paths)
            except Exception:
                return Response(
                    {'error': 'Path classification failed'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Choose the best path
            def choose_best_path(paths):
                risk_scores = {"High Risk": 3, "Low Risk": 2, "Safe": 1}
                scored_paths = sorted(paths, key=lambda x: risk_scores[x['risk']])
                return scored_paths[0]

            best_path = choose_best_path(classified_paths)

            # Return response
            return Response({
                'paths': classified_paths,
                'best_path': best_path
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BestPathDetailsView(APIView):
    def get(self, request, *args, **kwargs):
        session = request.session
        best_path = session.get('best_path', None)

        # If no best path exists in the session, return a 404 response
        if not best_path:
            return Response({'error': 'No best path found in session'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'best_path': best_path})
