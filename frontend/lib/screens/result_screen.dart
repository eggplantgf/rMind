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
      backgroundColor: const Color(0xFFF5F6F8),
      appBar: AppBar(
        title: Text(
          "분석 결과",
          style: TextStyle(color: Colors.black87, fontWeight: FontWeight.w700),
        ),
        iconTheme: IconThemeData(color: Colors.black87),
        backgroundColor: const Color(0xFFF5F6F8),
        elevation: 0,
        centerTitle: true,
        actions: [
          IconButton(
            icon: Icon(Icons.share_outlined),
            onPressed: () {
              // 공유 기능 (추후 구현)
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(SnackBar(content: Text('결과 공유하기 기능이 준비 중입니다.')));
            },
          ),
        ],
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
                  '발표 시간': '3분 32초',
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
                  '최고 긴장 구간': '01:40 ~ 02:21',
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
                  '큰 움직임': '1회 감지',
                  '손 제스처': '적절함',
                  '떨림': '거의 없음',
                },
              ),
              SizedBox(height: 32),

              // AI 코칭 어드바이스 섹션 추가
              _buildSectionTitle("🤖 AI 발표 코칭"),
              SizedBox(height: 12),
              _buildAdviceCard(),

              SizedBox(height: 32),

              // 추천 트레이닝 섹션 추가
              _buildSectionTitle("💡 맞춤형 트레이닝 추천"),
              SizedBox(height: 12),
              _buildRecommendationCard(),

              SizedBox(height: 40),

              // 하단 액션 버튼
              _buildActionButtons(),
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
          Padding(
            padding: EdgeInsets.symmetric(horizontal: 20),
            child: Text(
              description,
              style: TextStyle(color: Colors.grey[600], fontSize: 14),
            ),
          ),
          SizedBox(height: 16),
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
                ]..removeLast(),
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
        fit: BoxFit.contain,
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

  Widget _buildAdviceCard() {
    return Container(
      width: double.infinity,
      padding: EdgeInsets.all(24),
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
          _buildAdviceItem(
            icon: Icons.thumb_up_alt_rounded,
            color: Colors.blue,
            title: "잘한 점",
            content:
                "전반적으로 심박수의 변화가 크지 않고, 자세 안정성이 높습니다. 특히 영상 초반부의 시선 처리가 매우 자연스러워 청중의 집중을 잘 이끌어냈습니다.",
          ),
          Divider(height: 32, thickness: 1, color: Colors.grey[100]),
          _buildAdviceItem(
            icon: Icons.warning_rounded,
            color: Colors.orange,
            title: "보완할 점",
            content:
                "발표 중반부(01:40 이후)에 긴장도가 높아지면서 부자연스러운 동작이 감지되고, 눈 깜빡임 속도가 다소 빨라지는 경향이 있습니다. 문장 사이의 휴지(Pause)를 조금 더 길게 가져가보세요.",
          ),
          Divider(height: 32, thickness: 1, color: Colors.grey[100]),
          _buildAdviceItem(
            icon: Icons.tips_and_updates_rounded,
            color: Colors.purple,
            title: "총평 Advice",
            content:
                "전반적으로 훌륭한 발표였습니다! 긴장감 관리만 조금 더 신경 쓴다면 완벽할 거예요. 다음 연습 때는 '심호흡'을 의식적으로 해보세요.",
          ),
        ],
      ),
    );
  }

  Widget _buildAdviceItem({
    required IconData icon,
    required Color color,
    required String title,
    required String content,
  }) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            shape: BoxShape.circle,
          ),
          child: Icon(icon, color: color, size: 20),
        ),
        SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Colors.black87,
                ),
              ),
              SizedBox(height: 4),
              Text(
                content,
                style: TextStyle(
                  height: 1.5,
                  fontSize: 14,
                  color: Colors.grey[700],
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildRecommendationCard() {
    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: Row(
        children: [
          _buildTrainingCard(
            icon: Icons.mic_rounded,
            title: "발성 연습",
            subtitle: "목소리에 힘 싣기",
            color: Colors.blueAccent,
          ),
          SizedBox(width: 12),
          _buildTrainingCard(
            icon: Icons.timer_outlined,
            title: "페이스 조절",
            subtitle: "말하기 속도 훈련",
            color: Colors.orangeAccent,
          ),
          SizedBox(width: 12),
          _buildTrainingCard(
            icon: Icons.self_improvement,
            title: "긴장 완화",
            subtitle: "심호흡 가이드",
            color: Colors.teal,
          ),
        ],
      ),
    );
  }

  Widget _buildTrainingCard({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
  }) {
    return Container(
      width: 160,
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, color: color, size: 24),
          ),
          SizedBox(height: 16),
          Text(
            title,
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 16,
              color: Colors.black87,
            ),
          ),
          SizedBox(height: 4),
          Text(
            subtitle,
            style: TextStyle(fontSize: 12, color: Colors.grey[500]),
          ),
        ],
      ),
    );
  }

  Widget _buildActionButtons() {
    return Row(
      children: [
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {
              // 팝업 호출로 변경
              _showReportSaveDialog(context);
            },
            icon: Icon(Icons.download_rounded, color: Colors.black87),
            label: Text("리포트 저장", style: TextStyle(color: Colors.black87)),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.white,
              padding: EdgeInsets.symmetric(vertical: 16),
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
                side: BorderSide(color: Colors.grey[300]!),
              ),
            ),
          ),
        ),
        SizedBox(width: 16),
        Expanded(
          child: ElevatedButton.icon(
            onPressed: () {
              // 공유하기 기능 (Mock)
              ScaffoldMessenger.of(
                context,
              ).showSnackBar(SnackBar(content: Text('공유 링크가 복사되었습니다.')));
            },
            icon: Icon(Icons.share_rounded, color: Colors.white),
            label: Text("결과 공유", style: TextStyle(color: Colors.white)),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.blue[600], // 토스 브랜드 컬러 느낌
              padding: EdgeInsets.symmetric(vertical: 16),
              elevation: 0,
              shadowColor: Colors.blue[200],
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _showReportSaveDialog(BuildContext context) {
    // 초기 선택값 설정
    int selectedTension = 3; // 1~5
    String interviewExp = '없음';
    String practiceType = '연습';
    String sleepStatus = '보통';
    String caffeine = '안 마심';

    showDialog(
      context: context,
      builder: (BuildContext context) {
        return StatefulBuilder(
          builder: (context, setState) {
            return AlertDialog(
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(24),
              ),
              title: Column(
                children: [
                  Text(
                    "추가 정보 입력",
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 20),
                  ),
                  SizedBox(height: 8),
                  Text(
                    "더 정확한 분석 데이터 구축을 위해\n추가 정보를 선택해주세요.",
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                      height: 1.4,
                    ),
                  ),
                ],
              ),
              content: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _buildDialogSectionTitle("오늘의 긴장도 (1~5)"),
                    SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: List.generate(5, (index) {
                        int score = index + 1;
                        bool isSelected = selectedTension == score;
                        return InkWell(
                          onTap: () => setState(() => selectedTension = score),
                          child: Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? Colors.blue
                                  : Colors.grey[100],
                              shape: BoxShape.circle,
                              boxShadow: isSelected
                                  ? [
                                      BoxShadow(
                                        color: Colors.blue.withOpacity(0.3),
                                        blurRadius: 8,
                                        offset: Offset(0, 4),
                                      ),
                                    ]
                                  : [],
                            ),
                            alignment: Alignment.center,
                            child: Text(
                              "$score",
                              style: TextStyle(
                                color: isSelected
                                    ? Colors.white
                                    : Colors.grey[600],
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        );
                      }),
                    ),
                    SizedBox(height: 20),
                    _buildDialogSectionTitle("면접 경험"),
                    SizedBox(height: 8),
                    _buildChoiceChipRow(
                      ['없음', '1~2회', '3회 이상'],
                      interviewExp,
                      (val) => setState(() => interviewExp = val),
                    ),
                    SizedBox(height: 20),
                    _buildDialogSectionTitle("발표/면접 유형"),
                    SizedBox(height: 8),
                    _buildChoiceChipRow(
                      ['연습', '실전 리허설', '실전'],
                      practiceType,
                      (val) => setState(() => practiceType = val),
                    ),
                    SizedBox(height: 20),
                    _buildDialogSectionTitle("수면 상태"),
                    SizedBox(height: 8),
                    _buildChoiceChipRow(
                      ['부족', '보통', '충분'],
                      sleepStatus,
                      (val) => setState(() => sleepStatus = val),
                    ),
                    SizedBox(height: 20),
                    _buildDialogSectionTitle("카페인 섭취 여부"),
                    SizedBox(height: 8),
                    _buildChoiceChipRow(
                      ['안 마심', '마심'],
                      caffeine,
                      (val) => setState(() => caffeine = val),
                    ),
                  ],
                ),
              ),
              actionsPadding: EdgeInsets.fromLTRB(20, 0, 20, 20),
              actions: [
                Row(
                  children: [
                    Expanded(
                      child: TextButton(
                        onPressed: () => Navigator.pop(context),
                        style: TextButton.styleFrom(
                          padding: EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                            side: BorderSide(color: Colors.grey[300]!),
                          ),
                        ),
                        child: Text(
                          "취소",
                          style: TextStyle(color: Colors.grey[600]),
                        ),
                      ),
                    ),
                    SizedBox(width: 12),
                    Expanded(
                      child: ElevatedButton(
                        onPressed: () {
                          // TODO: 여기서 수집된 데이터를 DB로 전송하는 로직을 구현하면 됩니다.
                          // print('Tension: $selectedTension, Exp: $interviewExp...');

                          Navigator.pop(context); // 팝업 닫기
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text('소중한 데이터가 저장되었습니다.'),
                              backgroundColor: Colors.blue[700],
                              behavior: SnackBarBehavior.floating,
                            ),
                          );
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.blue[600],
                          padding: EdgeInsets.symmetric(vertical: 16),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          elevation: 0,
                        ),
                        child: Text(
                          "저장",
                          style: TextStyle(
                            color: Colors.white,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            );
          },
        );
      },
    );
  }

  Widget _buildDialogSectionTitle(String title) {
    return Text(
      title,
      style: TextStyle(
        fontSize: 14,
        fontWeight: FontWeight.w600,
        color: Colors.black87,
      ),
    );
  }

  Widget _buildChoiceChipRow(
    List<String> options,
    String currentValue,
    Function(String) onSelected,
  ) {
    return Wrap(
      spacing: 8,
      children: options.map((option) {
        bool isSelected = currentValue == option;
        return ChoiceChip(
          label: Text(
            option,
            style: TextStyle(
              color: isSelected ? Colors.white : Colors.grey[700],
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
              fontSize: 13,
            ),
          ),
          selected: isSelected,
          onSelected: (selected) {
            if (selected) onSelected(option);
          },
          selectedColor: Colors.blue[600],
          backgroundColor: Colors.grey[100],
          padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
            side: BorderSide(
              color: isSelected ? Colors.blue[600]! : Colors.grey[200]!,
            ),
          ),
        );
      }).toList(),
    );
  }
}
