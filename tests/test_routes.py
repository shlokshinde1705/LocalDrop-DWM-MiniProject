"""
Test Suite: Flask Application Route Verification
Tests that every registered endpoint returns HTTP 200 OK.
"""

import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_dashboard_route(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b"LocalDrop" in res.data


def test_orders_route(client):
    res = client.get('/orders')
    assert res.status_code == 200
    assert b"Operational Orders" in res.data


def test_products_route(client):
    res = client.get('/products')
    assert res.status_code == 200
    assert b"Product Catalog" in res.data


def test_customers_route(client):
    res = client.get('/customers')
    assert res.status_code == 200
    assert b"Customer" in res.data


def test_suppliers_route(client):
    res = client.get('/suppliers')
    assert res.status_code == 200
    assert b"Supplier" in res.data


def test_analytics_route(client):
    res = client.get('/analytics')
    assert res.status_code == 200
    assert b"Analytical SQL" in res.data


def test_olap_route(client):
    res = client.get('/olap')
    assert res.status_code == 200
    assert b"OLAP Operations" in res.data


def test_visualization_route(client):
    res = client.get('/visualization')
    assert res.status_code == 200
    assert b"Visualization Explorer" in res.data


def test_preprocessing_route(client):
    res = client.get('/data-preprocessing')
    assert res.status_code == 200
    assert b"Data Preprocessing" in res.data


def test_warehouse_route(client):
    res = client.get('/data-warehouse')
    assert res.status_code == 200
    assert b"Star Schema" in res.data


def test_mining_route(client):
    res = client.get('/data-mining')
    assert res.status_code == 200
    assert b"Data Mining" in res.data


def test_business_insights_route(client):
    res = client.get('/business-insights')
    assert res.status_code == 200
    assert b"Business Insights" in res.data
    assert b"How are sales" in res.data


def test_recommendations_route(client):
    res = client.get('/recommendations')
    assert res.status_code == 200
    assert b"Recommendations" in res.data
    assert b"Customer Groups" in res.data


def test_csv_export_routes(client):
    res = client.get('/export/csv/orders')
    assert res.status_code == 200
    assert res.headers['Content-Type'].startswith('text/csv')

    res_p = client.get('/export/csv/products')
    assert res_p.status_code == 200
    assert res_p.headers['Content-Type'].startswith('text/csv')


def test_store_home_route(client):
    res = client.get('/store')
    assert res.status_code == 200
    assert b"LocalDrop" in res.data
    assert b"Products from local suppliers" in res.data


def test_store_products_route(client):
    res = client.get('/store/products')
    assert res.status_code == 200
    assert b"Products" in res.data


def test_store_product_detail_route(client):
    res = client.get('/store/product/1')
    assert res.status_code == 200
    assert b"Supplier Information" in res.data


def test_store_suppliers_route(client):
    res = client.get('/store/suppliers')
    assert res.status_code == 200
    assert b"Suppliers" in res.data


def test_store_supplier_detail_route(client):
    res = client.get('/store/supplier/1')
    assert res.status_code == 200
    assert b"Supplier Profile" in res.data


def test_store_about_route(client):
    res = client.get('/store/about')
    assert res.status_code == 200
    assert b"About LocalDrop" in res.data
    assert b"Vidyalankar Institute of Technology" in res.data


def test_store_products_filter_and_sort(client):
    res = client.get('/store/products?q=Laptop&sort=price_asc')
    assert res.status_code == 200


def test_product_and_category_images(client):
    res_p = client.get('/static/images/products/product_40.jpg')
    assert res_p.status_code == 200
    assert res_p.headers['Content-Type'].startswith('image/jpeg')

    res_c = client.get('/static/images/categories/electronics.jpg')
    assert res_c.status_code == 200
    assert res_c.headers['Content-Type'].startswith('image/jpeg')


def test_featured_products_prioritization(client):
    res = client.get('/store')
    assert res.status_code == 200
    # Must contain verified imaged products in featured section
    assert b"product_1.jpg" in res.data or b"product_2.jpg" in res.data
    # Must not contain any placeholders or missing-image badges on storefront
    assert b"product-image-placeholder" not in res.data
    assert b"Photo coming soon" not in res.data

    res_p = client.get('/store/products')
    assert res_p.status_code == 200
    assert b"product-image-placeholder" not in res_p.data
    assert b"Photo coming soon" not in res_p.data
    assert b"Found <strong>15</strong> products" in res_p.data


def test_storefront_only_verified_products(client):
    """Storefront presentation layer must strictly expose products with verified photos."""
    verified_pids = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 40, 85, 92, 100}

    # Store products page 1
    res_p1 = client.get('/store/products?page=1')
    assert res_p1.status_code == 200
    assert b"product-image-placeholder" not in res_p1.data

    # Store products page 2
    res_p2 = client.get('/store/products?page=2')
    assert res_p2.status_code == 200
    assert b"product-image-placeholder" not in res_p2.data

    # Direct access to an unverified product must gracefully return 404
    res_unverified = client.get('/store/product/11')
    assert res_unverified.status_code == 404

    # Direct access to a verified product must return 200
    res_verified = client.get('/store/product/1')
    assert res_verified.status_code == 200
    assert b"product-image-placeholder" not in res_verified.data
    assert b"product_1.jpg" in res_verified.data

    # Operational DB and Admin catalog must retain all 120 SKUs
    res_admin = client.get('/products')
    assert res_admin.status_code == 200
    assert b"120 SKUs" in res_admin.data or b"Active SKUs: <strong>120</strong>" in res_admin.data


