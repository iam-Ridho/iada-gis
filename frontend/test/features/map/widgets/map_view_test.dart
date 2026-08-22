import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_map/flutter_map.dart';

import 'package:frontend/features/map/screens/widgets/map_view.dart';
import 'package:frontend/features/map/screens/widgets/map_bottom_sheet.dart';

// ---------------------------------------------------------------------------
// Dummy GeoJSON helpers
// ---------------------------------------------------------------------------

Map<String, dynamic> _makeGeoJson({String name = 'Test Area'}) => {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {"name": name},
          "geometry": {
            "type": "Polygon",
            "coordinates": [
              [
                [117.150, -0.500],
                [117.155, -0.500],
                [117.155, -0.505],
                [117.150, -0.505],
                [117.150, -0.500],
              ]
            ]
          }
        }
      ]
    };

/// Struktur nested seperti data ASLI dari backend (shapefile JIGD)
Map<String, dynamic> _makeMultiPolygonGeoJson({String name = 'Multi Area'}) => {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "properties": {"name": name},
          "geometry": {
            "type": "MultiPolygon",
            "coordinates": [
              // Polygon pertama
              [
                [
                  [117.150, -0.500],
                  [117.155, -0.500],
                  [117.155, -0.505],
                  [117.150, -0.505],
                  [117.150, -0.500],
                ]
              ],
              // Polygon kedua (bidang terpisah, masih dalam feature yang sama)
              [
                [
                  [117.160, -0.510],
                  [117.165, -0.510],
                  [117.165, -0.515],
                  [117.160, -0.515],
                  [117.160, -0.510],
                ]
              ],
            ]
          }
        }
      ]
    };

// ---------------------------------------------------------------------------
// Helper: bungkus widget dengan MaterialApp agar context tersedia
// ---------------------------------------------------------------------------

Widget _wrap(Widget child) => MaterialApp(home: Scaffold(body: child));

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

void main() {
  group('MapView Widget', () {
    testWidgets('render tanpa error dengan GeoJSON valid (Polygon)',
        (WidgetTester tester) async {
      await tester.pumpWidget(_wrap(MapView(geoJson: _makeGeoJson())));
      await tester.pump();
      expect(find.byType(FlutterMap), findsOneWidget);
    });

    testWidgets('render tanpa error dengan GeoJSON valid (MultiPolygon)',
        (WidgetTester tester) async {
      await tester.pumpWidget(_wrap(MapView(geoJson: _makeMultiPolygonGeoJson())));
      await tester.pump();
      expect(find.byType(FlutterMap), findsOneWidget);
      // Tidak boleh ada exception saat parsing MultiPolygon
    });

    testWidgets('render tanpa error dengan geoJson null',
        (WidgetTester tester) async {
      await tester.pumpWidget(_wrap(const MapView(geoJson: null)));
      await tester.pump();
      expect(find.byType(FlutterMap), findsOneWidget);
    });

    testWidgets('render tanpa error dengan features kosong',
        (WidgetTester tester) async {
      final emptyGeoJson = {"type": "FeatureCollection", "features": <dynamic>[]};
      await tester.pumpWidget(_wrap(MapView(geoJson: emptyGeoJson)));
      await tester.pump();
      expect(find.byType(FlutterMap), findsOneWidget);
    });

    testWidgets('update widget ketika geoJson berubah dari Polygon ke MultiPolygon',
        (WidgetTester tester) async {
      await tester.pumpWidget(_wrap(MapView(geoJson: _makeGeoJson(name: 'A'))));
      await tester.pump();

      await tester.pumpWidget(_wrap(MapView(geoJson: _makeMultiPolygonGeoJson(name: 'B'))));
      await tester.pump();

      expect(find.byType(FlutterMap), findsOneWidget);
    });

    testWidgets('showMapBottomSheet menampilkan MapView di BottomSheet',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (ctx) => ElevatedButton(
                onPressed: () => showMapBottomSheet(ctx, _makeGeoJson()),
                child: const Text('Open Map'),
              ),
            ),
          ),
        ),
      );

      await tester.tap(find.text('Open Map'));
      await tester.pumpAndSettle();

      expect(find.byType(MapView), findsOneWidget);
      expect(find.byType(FlutterMap), findsOneWidget);
    });
  });
}