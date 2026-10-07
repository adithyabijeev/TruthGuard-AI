from django.db.models import Avg
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .engine import analyze
from .models import Scan
from .serializers import AnalyzeSerializer, ScanSerializer

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'truthguard-api', 'version': '2.0.0'})

@api_view(['POST'])
def analyze_view(request):
    serializer = AnalyzeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    result = analyze(data.get('title', ''), data['content'], data.get('source', ''))
    scan = Scan.objects.create(
        title=data.get('title', ''), 
        content=data['content'], 
        source=data.get('source', ''), 
        risk_score=result['risk_score'], 
        severity=result['severity'], 
        verdict=result['verdict'], 
        analysis=result
    )
    return Response({'scan_id': scan.id, **result}, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def scans(request):
    limit = min(int(request.query_params.get('limit', 20)), 100)
    return Response(ScanSerializer(Scan.objects.all()[:limit], many=True).data)

@api_view(['GET'])
def stats(request):
    qs = Scan.objects.all()
    scans_list = list(qs)
    
    genuine_count = 0
    misleading_count = 0
    false_count = 0
    unverified_count = 0
    
    for s in scans_list:
        auth = (s.analysis or {}).get('content_authenticity', {})
        verdict = auth.get('verdict', '')
        if 'GENUINE' in verdict:
            genuine_count += 1
        elif 'MISLEADING' in verdict or 'MANIPULATED' in verdict:
            misleading_count += 1
        elif 'FALSE' in verdict:
            false_count += 1
        else:
            unverified_count += 1

    return Response({
        'total_scans': len(scans_list),
        'critical': qs.filter(severity='CRITICAL').count(),
        'high': qs.filter(severity='HIGH').count(),
        'medium': qs.filter(severity='MEDIUM').count(),
        'low': qs.filter(severity='LOW').count(),
        'average_risk': round(qs.aggregate(v=Avg('risk_score'))['v'] or 0, 1),
        'authenticity_stats': {
            'genuine': genuine_count,
            'misleading': misleading_count,
            'false': false_count,
            'unverified': unverified_count,
        }
    })
