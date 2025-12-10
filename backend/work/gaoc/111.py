from datetime import datetime
import logging
from db_configs import mongo_back as mongos  # 切换配置只需改这里的名字


# ======================
# 配置项
# ======================
DB_NAME = 'electric_bicycle'
COLLECTION_NAME = 'order'

# 日志配置（可选，便于排查问题）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'order_query_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ======================
# 核心查询函数
# ======================
def connect_mongodb():
    """连接MongoDB（沿用mongos模块的连接方式）"""
    try:
        db = mongos.mongo_connect()
        collection = db[DB_NAME][COLLECTION_NAME]
        # 验证连接
        collection.count_documents({}, limit=1)
        logger.info("✅ MongoDB连接成功（使用mongos模块）")
        return collection
    except Exception as e:
        logger.error(f"❌ MongoDB连接失败：{str(e)}", exc_info=True)
        raise

def query_orders_by_aggregate():
    """执行聚合查询，还原MongoDB Shell的聚合逻辑"""
    try:
        # 1. 连接数据库
        collection = connect_mongodb()

        # 2. 定义聚合管道（完全还原你的Shell聚合逻辑）
        pipeline = [
            # 步骤1：过滤符合条件的订单
            {
                "$match": {
                    "preEntryStatus": "COMPLETED",  # 上牌完成
                    "state": 1,  # 已验证（有效）
                    "buyer.idType": 2,  # 买家ID类型为2
                    "cancelled": False,  # 未取消
                    "createdDate": {"$lte": datetime.fromisoformat("2025-12-04T15:59:00+00:00")},  # 截止时间（UTC）
                    "userId": "69211df3f5a10065b74b43ae"  # 目标用户ID
                }
            },
            # 步骤2：转换userCounty为区域中文名称
            {
                "$addFields": {
                    "区域中文名称": {
                        "$switch": {
                            "branches": [
                                {"case": {"$eq": ["$userCounty", "330198"]}, "then": "浙江省杭州市杭州主城区"},
                                {"case": {"$eq": ["$userCounty", "330189"]}, "then": "浙江省杭州市杭州桐庐县"},
                                {"case": {"$eq": ["$userCounty", "330190"]}, "then": "浙江省杭州市杭州淳安县"},
                                {"case": {"$eq": ["$userCounty", "330191"]}, "then": "浙江省杭州市杭州富阳区"},
                                {"case": {"$eq": ["$userCounty", "330192"]}, "then": "浙江省杭州市杭州萧山区"},
                                {"case": {"$eq": ["$userCounty", "330193"]}, "then": "浙江省杭州市杭州建德区"},
                                {"case": {"$eq": ["$userCounty", "330194"]}, "then": "浙江省杭州市杭州临安区"},
                                {"case": {"$eq": ["$userCounty", "330195"]}, "then": "浙江省杭州市杭州临平区"},
                                {"case": {"$eq": ["$userCounty", "330196"]}, "then": "浙江省杭州市杭州钱塘区"},
                                {"case": {"$eq": ["$userCounty", "330197"]}, "then": "浙江省杭州市杭州余杭区"}
                            ],
                            "default": "未知区域"
                        }
                    }
                }
            },
            # 步骤3：格式化输出字段（只保留3个目标字段）
            {
                "$project": {
                    "_id": 0,  # 隐藏默认_id
                    "区域中文名称": 1,
                    "车架号": "$frameNumber",
                    "号牌": "$numberPlate"
                }
            },
            # 步骤4：按区域名称升序排序
            {
                "$sort": {"区域中文名称": 1}
            }
        ]

        # 3. 执行聚合查询
        logger.info("🚀 开始执行聚合查询...")
        result = list(collection.aggregate(pipeline))  # 转换为列表便于处理

        # 4. 输出查询结果
        logger.info(f"✅ 查询完成，共匹配到 {len(result)} 条数据")
        print(f"\n📊 查询结果汇总：共匹配到 {len(result)} 条数据")
        print("=" * 80)
        
        # 打印每条结果（格式化输出）
        for idx, item in enumerate(result, 1):
            print(f"[{idx}] 区域：{item.get('区域中文名称', '未知区域')} | 车架号：{item.get('车架号', '-')} | 号牌：{item.get('号牌', '-')}")
        
        return result

    except Exception as e:
        logger.error(f"❌ 查询执行失败：{str(e)}", exc_info=True)
        print(f"\n❌ 查询执行失败：{str(e)}")
        raise

# ======================
# 主函数
# ======================
def main():
    print("=" * 80)
    print("📋 开始执行订单聚合查询脚本")
    print(f"🔍 查询条件：userId=69211df3f5a10065b74b43ae，上牌完成，截止时间2025-12-04 15:59")
    print("=" * 80)
    
    # 执行查询
    query_result = query_orders_by_aggregate()
    
    # 可选：将结果保存为CSV文件
    save_to_csv = input("\n📌 是否将查询结果保存为CSV文件？(y/n)：").strip()
    if save_to_csv.lower() == 'y':
        csv_path = f"order_query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            import csv
            with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["区域中文名称", "车架号", "号牌"])
                writer.writeheader()
                writer.writerows(query_result)
            logger.info(f"📁 查询结果已保存到：{csv_path}")
            print(f"\n✅ 查询结果已保存到：{csv_path}")
        except Exception as e:
            logger.error(f"❌ 保存CSV失败：{str(e)}", exc_info=True)
            print(f"\n❌ 保存CSV失败：{str(e)}")

    print("\n🎉 脚本执行完毕！")

# ======================
# 程序入口
# ======================
if __name__ == "__main__":
    main()