import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../widgets/rmind_widgets.dart';
import '../services/api_service.dart';
import 'my_page_screen.dart';

class ResultPage extends StatefulWidget {
  final String videoPath;
  final Map<String, dynamic>? analysisResult;

  ResultPage({required this.videoPath, this.analysisResult});

  @override
  _ResultPageState createState() => _ResultPageState();
}

class _ResultPageState extends State<ResultPage> {
  int selectedIndex = 1;
  Map<String, Uint8List?> _downloadedImages = {};
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    if (widget.analysisResult != null) {
      _downloadImages();
    }
  }

  Future<void> _downloadImages() async {
    if (widget.analysisResult == null) return;

    setState(() => _isLoading = true);

    final videoId = widget.analysisResult!['video_id'] as String;
    final imageTypes = ['bpm', 'blink', 'motion', 'combined'];

    for (String imageType in imageTypes) {
      try {
        final imageData = await ApiService.downloadImage(videoId, imageType);
        if (imageData != null) {
          _downloadedImages[imageType] = imageData;
        }
      } catch (e) {
        print('Failed to download $imageType image: $e');
      }
    }

    setState(() => _isLoading = false);
  }

  Future<void> _handleRefresh() async {
    if (widget.analysisResult != null) {
      await _downloadImages();
    } else {
      await Future.delayed(Duration(seconds: 1));
    }
    setState(() {});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F6F8), // 부드러운 회색 배경 (토스 스타일)
      appBar: AppBar(
        title: Text(
          "분석 결과",
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.w700),
        ),
        iconTheme: IconThemeData(color: Colors.black87),
        backgroundColor: const Color(0xFFF5F6F8),
        elevation: 0,
        centerTitle: true,
      ),
      body: RefreshIndicator(
        onRefresh: _handleRefresh,
        child: SingleChildScrollView(
          physics: AlwaysScrollableScrollPhysics(),
          padding: EdgeInsets.symmetric(horizontal: 20, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeaderSection(),
              SizedBox(height: 24),
              _buildSectionTitle("종합 분석"),
              SizedBox(height: 12),
              _buildResultCard(
                title: "🌱 총 결과",
                color: Colors.green,
                description: "전반적인 발표 능력을 종합적으로 평가한 결과입니다.",
                stats: {
                  '종합 점수': '85점',
                  '주요 감정': '약간 긴장',
                  '발표 시간': '12분 30초',
                  '전달력': '우수함',
                },
              ),
              SizedBox(height: 24),
              _buildSectionTitle("세부 지표 분석"),
              SizedBox(height: 12),
              _buildResultCard(
                title: "❤️ 심박수 (BPM)",
                color: Colors.redAccent,
                description: "발표 중 심박수 변화를 통해 긴장도를 측정합니다.",
                stats: {
                  '평균 심박수': '95 BPM',
                  '최고 심박수': '120 BPM',
                  '긴장 구간': '02:15 ~ 02:45',
                  '안정도': '보통',
                },
              ),
              SizedBox(height: 16),
              _buildResultCard(
                title: "👁 눈 깜빡임",
                color: Colors.deepPurple,
                description: "눈 깜빡임 빈도를 통해 집중도와 불안감을 분석합니다.",
                stats: {
                  '분당 깜빡임': '15회',
                  '시선 고정': '양호',
                  '피로도': '낮음',
                  '집중도': '높음',
                },
              ),
              SizedBox(height: 16),
              _buildResultCard(
                title: "💃 몸의 움직임",
                color: Colors.teal[700]!,
                description: "불필요한 움직임이나 제스처의 적절성을 파악합니다.",
                stats: {
                  '자세 안정성': '높음',
                  '큰 움직임': '3회 감지',
                  '손 제스처': '적절함',
                  '떨림': '거의 없음',
                },
              ),
              SizedBox(height: 40),
            ],
          ),
        ),
      ),
      bottomNavigationBar: RMindBottomNavBar(
        selectedIndex: selectedIndex,
        onItemTapped: (index) {
          if (index == 2) {
            Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => MyPageScreen()),
            );
          } else {
            setState(() => selectedIndex = index);
          }
        },
      ),
    );
  }

  Widget _buildHeaderSection() {
    return Container(
      padding: EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 20,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        children: [
          Image.asset(
            'assets/images/logo.png',
            width: 80,
            height: 80,
            fit: BoxFit.contain,
          ),
          SizedBox(height: 16),
          Text(
            '현재 긴장 상태',
            style: TextStyle(
              fontSize: 16,
              color: Colors.grey[600],
              fontWeight: FontWeight.w600,
            ),
          ),
          SizedBox(height: 8),
          Text(
            '다소 긴장 상태입니다',
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 20),
          Image.asset(
            'assets/images/tension_bar.png',
            width: double.infinity,
            fit: BoxFit.fitWidth,
          ),
          SizedBox(height: 16),
          Container(
            padding: EdgeInsets.symmetric(vertical: 12, horizontal: 16),
            decoration: BoxDecoration(
              color: Colors.red[50],
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(Icons.info_outline, color: Colors.red[400], size: 20),
                SizedBox(width: 12),
                Expanded(
                  child: Text(
                    "심호흡을 크게 3번 하고, 어깨의 힘을 빼보세요. 훨씬 편안해질 거예요.",
                    style: TextStyle(
                      color: Colors.red[700],
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.bold,
          color: Colors.black87,
        ),
      ),
    );
  }

  Widget _buildResultCard({
    required String title,
    required Color color,
    required String description,
    required Map<String, String> stats,
  }) {
    String imageType;
    String fallbackAssetPath;

    if (title.contains('총 결과')) {
      imageType = 'combined';
      fallbackAssetPath = 'assets/images/overall.png';
    } else if (title.contains('심박수')) {
      imageType = 'bpm';
      fallbackAssetPath = 'assets/images/bpm_ex.png';
    } else if (title.contains('눈 깜빡임')) {
      imageType = 'blink';
      fallbackAssetPath = 'assets/images/blink_ex.png';
    } else if (title.contains('몸의 움직임')) {
      imageType = 'motion';
      fallbackAssetPath = 'assets/images/motion_ex.png';
    } else {
      imageType = '';
      fallbackAssetPath = 'assets/images/logo.png';
    }

    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 15,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: EdgeInsets.fromLTRB(20, 20, 20, 12),
            child: Row(
              children: [
                Container(
                  padding: EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: color.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Icon(Icons.insights, color: color, size: 20),
                ),
                SizedBox(width: 12),
                Text(
                  title,
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 18,
                    color: Colors.black87,
                  ),
                ),
                Spacer(),
                if (_isLoading)
                  SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
          ),
          
          // Description
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 20),
            child: Text(
              description,
              style: TextStyle(color: Colors.grey[600], fontSize: 14),
            ),
          ),
          SizedBox(height: 16),

          // Graph Image Area
          Container(
            width: double.infinity,
            height: 200,
            margin: EdgeInsets.symmetric(horizontal: 20),
            decoration: BoxDecoration(
              color: Colors.grey[50],
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.grey[200]!),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: _buildImageWidget(imageType, fallbackAssetPath),
            ),
          ),
          
          SizedBox(height: 20),
          
          // Stats Grid
          Padding(
            padding: EdgeInsets.fromLTRB(20, 0, 20, 24),
            child: Container(
              padding: EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFFF8F9FA),
                borderRadius: BorderRadius.circular(16),
              ),
              child: Column(
                children: [
                  for (var entry in stats.entries)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            entry.key,
                            style: TextStyle(
                              color: Colors.grey[600],
                              fontSize: 14,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                          Text(
                            entry.value,
                            style: TextStyle(
                              color: Colors.black87,
                              fontSize: 15,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                    ),
                ]..removeLast(), // 마지막 아이템의 padding bottom 제거 효과를 위해 로직 조정이 필요하지만, 단순화를 위해 유지하거나 조정.
                  // 리스트의 마지막 요소 처리가 복잡하니 그냥 둠. 대신 마지막 아이템 뒤 SizedBox 제거를 위해 for문 사용.
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildImageWidget(String imageType, String fallbackAssetPath) {
    if (widget.analysisResult != null &&
        _downloadedImages.containsKey(imageType) &&
        _downloadedImages[imageType] != null) {
      return Image.memory(
        _downloadedImages[imageType]!,
        width: double.infinity,
        height: double.infinity,
        fit: BoxFit.contain, // 그래프 전체가 보이도록 contain으로 변경
        errorBuilder: (context, error, stackTrace) {
          return Image.asset(
            fallbackAssetPath,
            width: double.infinity,
            height: double.infinity,
            fit: BoxFit.contain,
          );
        },
      );
    }

    return Image.asset(
      fallbackAssetPath,
      width: double.infinity,
      height: double.infinity,
      fit: BoxFit.contain,
    );
  }
}
