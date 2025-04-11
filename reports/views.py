from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.db import transaction
from django.http import HttpResponse
from datetime import datetime
from io import BytesIO, StringIO
import csv
from reportlab.pdfgen import canvas
from core.models import LoggerService
from .models import Report
from .serializers import ReportSerializer
from orders.models import Order, OrderItem
from products.models import Product

class ReportListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        try:
            reports = Report.objects.all().order_by('-created_at')
            serializer = ReportSerializer(reports, many=True)
            return Response(serializer.data)
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Report',
                description='Error on list reports: ' + str(e)
            )
            raise e

class ReportCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        with transaction.atomic():
            try:
                serializer = ReportSerializer(data=request.data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                report_obj = serializer.save(user=request.user if request.user.is_authenticated else None)
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='CREATE',
                    table_name='Report',
                    description='Created report ' + str(report_obj.id)
                )
                if report_obj.report_type == 'sales_by_customer':
                    data = self.generate_sales_by_customer_data(report_obj.start_date, report_obj.end_date)
                    return Response(data)
                if report_obj.report_type == 'best_sellers':
                    data = self.generate_best_sellers_data(report_obj.start_date, report_obj.end_date)
                    return Response(data)
                return Response({"detail": "Unknown report type"}, status=400)
            except Exception as e:
                LoggerService.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    action='ERROR',
                    table_name='Report',
                    description='Error on create report: ' + str(e)
                )
                raise e

    def generate_sales_by_customer_data(self, start_date, end_date):
        orders = Order.objects.filter(created_at__range=[start_date, end_date]).select_related('user')
        result = []
        for o in orders:
            result.append({
                'order_id': o.id,
                'customer': o.user.email if o.user else '',
                'total_amount': float(o.total_amount),
                'created_at': o.created_at
            })
        return result

    def generate_best_sellers_data(self, start_date, end_date):
        items = OrderItem.objects.filter(created_at__range=[start_date, end_date])
        product_counts = {}
        for i in items:
            product_counts[i.product_id] = product_counts.get(i.product_id, 0) + i.quantity
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
        result = []
        for pid, qty in sorted_products:
            p = Product.objects.filter(id=pid).first()
            if p:
                result.append({
                    'product_id': p.id,
                    'product_name': p.name,
                    'quantity_sold': qty
                })
        return result

class ReportPDFView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, report_id):
        try:
            report_obj = Report.objects.filter(id=report_id).first()
            if not report_obj:
                return Response({"detail": "Report not found"}, status=404)
            buffer = BytesIO()
            p = canvas.Canvas(buffer)
            p.drawString(100, 800, "Report " + str(report_obj.id) + ": " + report_obj.name)
            p.showPage()
            p.save()
            buffer.seek(0)
            response = HttpResponse(buffer, content_type='application/pdf')
            filename = report_obj.name.replace(' ', '_') + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"
            response['Content-Disposition'] = 'attachment; filename="' + filename + '"'
            return response
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Report',
                description='Error on get PDF report: ' + str(e)
            )
            raise e

class ReportExcelView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, report_id):
        try:
            report_obj = Report.objects.filter(id=report_id).first()
            if not report_obj:
                return Response({"detail": "Report not found"}, status=404)
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(["Report ID", "Name", "Type", "Start Date", "End Date", "Created At"])
            writer.writerow([
                report_obj.id,
                report_obj.name,
                report_obj.report_type,
                report_obj.start_date,
                report_obj.end_date,
                report_obj.created_at
            ])
            response = HttpResponse(output.getvalue(), content_type='text/csv')
            filename = report_obj.name.replace(' ', '_') + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
            response['Content-Disposition'] = 'attachment; filename=\"" + filename + "\"'
            return response
        except Exception as e:
            LoggerService.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action='ERROR',
                table_name='Report',
                description='Error on get Excel report: ' + str(e)
            )
            raise e
