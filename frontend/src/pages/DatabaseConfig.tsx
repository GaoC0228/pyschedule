import React, { useState, useEffect } from 'react';
import {
  Card, Button, Table, Modal, Form, Input, Select, message,
  Space, Popconfirm, Tag, Typography, Switch
} from 'antd';
import {
  DatabaseOutlined, PlusOutlined, EditOutlined, DeleteOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ThunderboltOutlined,
  CopyOutlined, CodeOutlined
} from '@ant-design/icons';
import api from '../api/axios';
import type { ColumnsType } from 'antd/es/table';

const { TextArea } = Input;
const { Option } = Select;
const { Text } = Typography;

interface DatabaseConfig {
  id: number;
  name: string;
  display_name: string;
  db_type: string;
  environment: string;
  host: string;
  port?: number;
  username?: string;
  password?: string;
  database?: string;
  connection_string?: string;
  replica_set?: string;
  auth_source?: string;
  description?: string;
  is_active: boolean;
  is_public: boolean;  // 是否公开
  created_by?: string;  // 创建者
  created_at: string;
}

const DatabaseConfig: React.FC = () => {
  const [configs, setConfigs] = useState<DatabaseConfig[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState<DatabaseConfig | null>(null);
  const [testLoading, setTestLoading] = useState<number | null>(null);
  const [selectedDbType, setSelectedDbType] = useState<string>('');
  const [useConnectionString, setUseConnectionString] = useState<boolean>(false);
  const [modalTestLoading, setModalTestLoading] = useState(false);
  const [testPassed, setTestPassed] = useState(false);
  const [form] = Form.useForm();

  // 加载配置列表
  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await api.get('/database-configs');
      setConfigs(response.data);
    } catch (error: any) {
      message.error('加载配置失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  // 隐藏连接字符串中的密码
  const maskConnectionString = (connStr: string): string => {
    if (!connStr) return connStr;
    // 匹配 mongodb://username:password@host 格式
    const regex = /^(mongodb(?:\+srv)?:\/\/[^:]+:)([^@]+)(@.+)$/;
    const match = connStr.match(regex);
    if (match) {
      // 替换密码为星号
      return `${match[1]}******${match[3]}`;
    }
    return connStr;
  };

  // 打开新建/编辑对话框
  const handleOpenModal = (config?: DatabaseConfig) => {
    setTestPassed(false); // 重置测试状态
    if (config) {
      setEditingConfig(config);
      setSelectedDbType(config.db_type);
      // 判断是否使用连接字符串
      setUseConnectionString(!!config.connection_string);
      // 编辑时不回显密码（密码已加密）
      const { password, connection_string, ...configWithoutPassword } = config;
      // 隐藏连接字符串中的密码
      const maskedConnectionString = connection_string ? maskConnectionString(connection_string) : undefined;
      form.setFieldsValue({
        ...configWithoutPassword,
        connection_string: maskedConnectionString
      });
    } else {
      setEditingConfig(null);
      setSelectedDbType('');
      setUseConnectionString(false);
      form.resetFields();
      // 设置默认值
      form.setFieldsValue({ is_public: false, is_active: true });
    }
    setModalVisible(true);
  };

  // 对话框内测试连接
  const handleModalTest = async () => {
    try {
      const values = await form.validateFields();
      setModalTestLoading(true);
      
      // 如果是编辑模式且连接字符串包含******，说明密码未修改，需要从原配置获取
      const testValues = { ...values };
      if (editingConfig && testValues.connection_string && testValues.connection_string.includes('******')) {
        testValues.connection_string = editingConfig.connection_string;
      }
      
      const response = await api.post('/database-configs/test-direct', testValues);
      
      if (response.data.success) {
        message.success('✅ 连接测试成功！');
        setTestPassed(true);
      } else {
        message.error('❌ 连接测试失败: ' + response.data.message);
        setTestPassed(false);
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误';
      message.error('❌ 连接测试失败: ' + errorMsg);
      setTestPassed(false);
    } finally {
      setModalTestLoading(false);
    }
  };

  // 保存配置
  const handleSave = async () => {
    // 新建配置时必须先测试通过
    if (!editingConfig && !testPassed) {
      message.warning('请先测试连接，确保配置正确后再保存');
      return;
    }
    
    try {
      const values = await form.validateFields();
      
      // 如果是编辑模式且连接字符串包含******，说明密码未修改，需要从原配置获取
      if (editingConfig && values.connection_string && values.connection_string.includes('******')) {
        values.connection_string = editingConfig.connection_string;
      }
      
      if (editingConfig) {
        // 更新
        await api.put(`/database-configs/${editingConfig.name}`, values);
        message.success('配置更新成功');
      } else {
        // 新建
        await api.post('/database-configs', values);
        message.success('配置创建成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      setTestPassed(false);
      loadConfigs();
    } catch (error: any) {
      if (error.errorFields) {
        message.error('请检查表单填写');
      } else {
        // 处理422验证错误
        if (error.response?.status === 422) {
          const detail = error.response?.data?.detail;
          if (Array.isArray(detail)) {
            // Pydantic验证错误格式
            const errors = detail.map((err: any) => `${err.loc.join('.')}: ${err.msg}`).join('; ');
            message.error('数据验证失败: ' + errors);
          } else if (typeof detail === 'string') {
            message.error('数据验证失败: ' + detail);
          } else {
            message.error('数据验证失败，请检查输入');
          }
        } else {
          const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误';
          message.error('保存失败: ' + errorMsg);
        }
      }
    }
  };

  // 删除配置
  const handleDelete = async (name: string) => {
    try {
      await api.delete(`/database-configs/${name}`);
      message.success('配置删除成功');
      loadConfigs();
    } catch (error: any) {
      message.error('删除失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 复制配置
  const handleCopy = (config: DatabaseConfig) => {
    const { id, name, created_at, ...configData } = config;
    // 生成新的配置名称
    const newName = `${name}_copy`;
    form.setFieldsValue({
      ...configData,
      name: newName,
      display_name: `${config.display_name} (副本)`
    });
    setEditingConfig(null);
    setSelectedDbType(config.db_type);
    setUseConnectionString(!!config.connection_string);
    setModalVisible(true);
    message.info('已复制配置，请修改配置名称后保存');
  };

  // 显示使用示例
  const handleShowUsage = (config: DatabaseConfig) => {
    const usageCode = generateUsageCode(config);
    Modal.info({
      title: `📖 使用示例 - ${config.display_name}`,
      width: 800,
      content: (
        <div>
          <p style={{ marginBottom: 12 }}>在工作台的Python脚本中使用此数据库配置：</p>
          <div style={{ background: '#f5f5f5', padding: 16, borderRadius: 4, marginBottom: 12 }}>
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {usageCode}
            </pre>
          </div>
          <Button 
            type="primary" 
            icon={<CopyOutlined />}
            onClick={() => {
              navigator.clipboard.writeText(usageCode);
              message.success('代码已复制到剪贴板');
            }}
          >
            复制代码
          </Button>
        </div>
      )
    });
  };

  // 生成使用示例代码
  const generateUsageCode = (config: DatabaseConfig): string => {
    const examples: Record<string, string> = {
      mongodb: `# MongoDB 使用示例
# 注意：db_configs 模块会自动管理Python路径，无需手动设置sys.path
from db_configs import ${config.name} as mongos  # 切换配置只需改这里的名字

# 获取数据库连接（client已自动创建）
client = mongos.client
db = client['${config.database || 'your_database'}']

# 查询示例
collection = db['your_collection']
results = collection.find({'status': 'active'})
for doc in results:
    print(doc)

# 插入示例
collection.insert_one({'name': 'test', 'value': 123})

# 关闭连接
client.close()`,
      
      mysql: `# MySQL 使用示例
from backend.work.db_manager import get_db_connection

# 获取数据库连接
connection = get_db_connection('${config.name}')
cursor = connection.cursor()

# 查询示例
cursor.execute("SELECT * FROM your_table WHERE status = %s", ('active',))
results = cursor.fetchall()
for row in results:
    print(row)

# 插入示例
cursor.execute("INSERT INTO your_table (name, value) VALUES (%s, %s)", ('test', 123))
connection.commit()

# 关闭连接
cursor.close()
connection.close()`,
      
      postgresql: `# PostgreSQL 使用示例
from backend.work.db_manager import get_db_connection

# 获取数据库连接
connection = get_db_connection('${config.name}')
cursor = connection.cursor()

# 查询示例
cursor.execute("SELECT * FROM your_table WHERE status = %s", ('active',))
results = cursor.fetchall()
for row in results:
    print(row)

# 插入示例
cursor.execute("INSERT INTO your_table (name, value) VALUES (%s, %s)", ('test', 123))
connection.commit()

# 关闭连接
cursor.close()
connection.close()`,
      
      redis: `# Redis 使用示例
from backend.work.db_manager import get_db_connection

# 获取Redis连接
r = get_db_connection('${config.name}')

# 字符串操作
r.set('key', 'value')
value = r.get('key')
print(value)

# 哈希操作
r.hset('user:1', 'name', 'John')
r.hset('user:1', 'age', 30)
user = r.hgetall('user:1')
print(user)

# 列表操作
r.lpush('tasks', 'task1', 'task2')
tasks = r.lrange('tasks', 0, -1)
print(tasks)`
    };

    return examples[config.db_type] || '# 暂无示例';
  };

  // 测试连接
  const handleTest = async (config: DatabaseConfig) => {
    setTestLoading(config.id);
    try {
      const response = await api.post('/database-configs/test', {
        config_name: config.name
      });
      
      if (response.data.success) {
        const details = response.data.details;
        Modal.success({
          title: '✅ 连接成功',
          width: 600,
          content: (
            <div>
              <p style={{ fontSize: 16, marginBottom: 16 }}>{response.data.message}</p>
              {details && (
                <div style={{ background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 4, padding: 16 }}>
                  <h4 style={{ marginTop: 0, color: '#52c41a' }}>📊 数据库信息</h4>
                  {details.version && (
                    <p><strong>版本：</strong>{details.version}</p>
                  )}
                  {details.server_info && (
                    <p><strong>服务器版本：</strong>{details.server_info}</p>
                  )}
                  {details.current_database && (
                    <p><strong>当前数据库：</strong>{details.current_database}</p>
                  )}
                  {details.databases && (
                    <div>
                      <p><strong>可用数据库（{details.databases.length}个）：</strong></p>
                      <div style={{ maxHeight: 150, overflow: 'auto', background: '#fff', padding: 8, borderRadius: 4 }}>
                        {details.databases.map((db: string, index: number) => (
                          <div key={index} style={{ padding: '4px 8px', borderBottom: '1px solid #f0f0f0' }}>
                            📁 {db}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {details.mode && (
                    <p><strong>运行模式：</strong>{details.mode}</p>
                  )}
                  {details.used_memory && (
                    <p><strong>内存使用：</strong>{details.used_memory}</p>
                  )}
                  {details.connected_clients !== undefined && (
                    <p><strong>连接客户端：</strong>{details.connected_clients}</p>
                  )}
                  {details.db_keys !== undefined && (
                    <p><strong>键总数：</strong>{details.db_keys}</p>
                  )}
                </div>
              )}
            </div>
          )
        });
      } else {
        Modal.error({
          title: '❌ 连接失败',
          width: 600,
          content: (
            <div>
              <p style={{ fontSize: 16, color: '#ff4d4f', marginBottom: 12 }}>
                <strong>错误信息：</strong>
              </p>
              <div style={{ 
                background: '#fff2f0', 
                border: '1px solid #ffccc7', 
                borderRadius: 4, 
                padding: 12,
                wordBreak: 'break-word'
              }}>
                {response.data.message}
              </div>
              <p style={{ marginTop: 12, fontSize: 12, color: '#8c8c8c' }}>
                💡 请检查：
                <br />• 主机地址和端口是否正确
                <br />• 用户名和密码是否正确
                <br />• 数据库服务是否正在运行
                <br />• 网络连接是否正常
                <br />• 防火墙是否允许连接
              </p>
            </div>
          )
        });
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || '未知错误';
      Modal.error({
        title: '❌ 测试失败',
        width: 600,
        content: (
          <div>
            <p style={{ fontSize: 16, color: '#ff4d4f', marginBottom: 12 }}>
              <strong>请求失败：</strong>
            </p>
            <div style={{ 
              background: '#fff2f0', 
              border: '1px solid #ffccc7', 
              borderRadius: 4, 
              padding: 12,
              wordBreak: 'break-word'
            }}>
              {errorMsg}
            </div>
          </div>
        )
      });
    } finally {
      setTestLoading(null);
    }
  };

  // 表格列定义
  const columns: ColumnsType<DatabaseConfig> = [
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
      fixed: 'left',
      render: (text) => <Text strong>{text}</Text>
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
      width: 150
    },
    {
      title: '数据库类型',
      dataIndex: 'db_type',
      key: 'db_type',
      width: 120,
      render: (type) => {
        const colors: Record<string, string> = {
          mongodb: 'green',
          mysql: 'blue',
          postgresql: 'purple',
          redis: 'red'
        };
        return <Tag color={colors[type] || 'default'}>{type.toUpperCase()}</Tag>;
      }
    },
    {
      title: '环境',
      dataIndex: 'environment',
      key: 'environment',
      width: 100,
      render: (env) => {
        const colors: Record<string, string> = {
          production: 'red',
          test: 'orange',
          dev: 'green'
        };
        return <Tag color={colors[env] || 'default'}>{env}</Tag>;
      }
    },
    {
      title: '主机地址',
      dataIndex: 'host',
      key: 'host',
      width: 200,
      ellipsis: true
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 80
    },
    {
      title: '数据库',
      dataIndex: 'database',
      key: 'database',
      width: 120,
      ellipsis: true
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (active) => active ? (
        <Tag icon={<CheckCircleOutlined />} color="success">启用</Tag>
      ) : (
        <Tag icon={<CloseCircleOutlined />} color="default">禁用</Tag>
      )
    },
    {
      title: '权限',
      dataIndex: 'is_public',
      key: 'is_public',
      width: 80,
      render: (isPublic) => isPublic ? (
        <Tag color="blue">公开</Tag>
      ) : (
        <Tag color="default">私有</Tag>
      )
    },
    {
      title: '创建者',
      dataIndex: 'created_by',
      key: 'created_by',
      width: 100,
      render: (createdBy) => createdBy || '-'
    },
    {
      title: '操作',
      key: 'action',
      fixed: 'right',
      width: 300,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<ThunderboltOutlined />}
            onClick={() => handleTest(record)}
            loading={testLoading === record.id}
          >
            测试
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CodeOutlined />}
            onClick={() => handleShowUsage(record)}
          >
            示例
          </Button>
          <Button
            type="link"
            size="small"
            icon={<CopyOutlined />}
            onClick={() => handleCopy(record)}
          >
            复制
          </Button>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            编辑
          </Button>
          <Popconfirm
            title="确定要删除这个配置吗？"
            onConfirm={() => handleDelete(record.name)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={
          <Space>
            <DatabaseOutlined />
            <span>数据库配置管理</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => handleOpenModal()}
          >
            新建配置
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条配置`
          }}
        />
      </Card>

      {/* 新建/编辑对话框 */}
      <Modal
        title={editingConfig ? '编辑数据库配置' : '新建数据库配置'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setTestPassed(false);
        }}
        width={800}
        footer={[
          <Button key="cancel" onClick={() => {
            setModalVisible(false);
            form.resetFields();
            setTestPassed(false);
          }}>
            取消
          </Button>,
          <Button
            key="test"
            icon={<ThunderboltOutlined />}
            onClick={handleModalTest}
            loading={modalTestLoading}
          >
            测试连接
          </Button>,
          <Button
            key="save"
            type="primary"
            onClick={handleSave}
            disabled={!editingConfig && !testPassed}
          >
            保存
          </Button>
        ]}
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_active: true,
            environment: 'production'
          }}
        >
          <Form.Item
            label="配置名称"
            name="name"
            rules={[
              { required: true, message: '请输入配置名称' },
              { pattern: /^[a-z0-9_]+$/, message: '只能包含小写字母、数字和下划线' }
            ]}
            extra="唯一标识，用于脚本中引用，如: mongodb_prod"
          >
            <Input placeholder="mongodb_prod" disabled={!!editingConfig} />
          </Form.Item>

          <Form.Item
            label="显示名称"
            name="display_name"
            rules={[{ required: true, message: '请输入显示名称' }]}
          >
            <Input placeholder="生产环境MongoDB" />
          </Form.Item>

          <Form.Item
            label="数据库类型"
            name="db_type"
            rules={[{ required: true, message: '请选择数据库类型' }]}
          >
            <Select 
              placeholder="选择数据库类型"
              onChange={(value) => setSelectedDbType(value)}
            >
              <Option value="mongodb">MongoDB</Option>
              <Option value="mysql">MySQL</Option>
              <Option value="postgresql">PostgreSQL</Option>
              <Option value="redis">Redis</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="环境"
            name="environment"
            rules={[{ required: true, message: '请选择环境' }]}
          >
            <Select placeholder="选择环境">
              <Option value="production">生产环境</Option>
              <Option value="test">测试环境</Option>
              <Option value="dev">开发环境</Option>
            </Select>
          </Form.Item>

          {/* MongoDB连接方式选择 */}
          {selectedDbType === 'mongodb' && (
            <Form.Item label="连接方式">
              <Select 
                value={useConnectionString ? 'connection_string' : 'host_port'}
                onChange={(value) => {
                  setUseConnectionString(value === 'connection_string');
                  // 切换时清空相关字段
                  if (value === 'connection_string') {
                    form.setFieldsValue({ host: undefined, port: undefined, username: undefined, password: undefined });
                  } else {
                    form.setFieldsValue({ connection_string: undefined });
                  }
                }}
              >
                <Option value="host_port">主机地址连接</Option>
                <Option value="connection_string">连接字符串</Option>
              </Select>
            </Form.Item>
          )}

          {/* MongoDB连接字符串方式 */}
          {selectedDbType === 'mongodb' && useConnectionString && (
            <Form.Item
              label="MongoDB连接字符串"
              name="connection_string"
              rules={[{ required: true, message: '请输入MongoDB连接字符串' }]}
              extra={editingConfig && form.getFieldValue('connection_string')?.includes('******') 
                ? "密码已隐藏，如需修改请重新输入完整连接字符串" 
                : "格式: mongodb://user:pass@host:27017/dbname?replicaSet=rs0&authSource=admin"}
            >
              <Input.TextArea 
                placeholder="mongodb://user:pass@host:27017/dbname" 
                rows={3}
                autoSize={{ minRows: 2, maxRows: 4 }}
              />
            </Form.Item>
          )}

          {/* 主机地址连接方式 */}
          {(!selectedDbType || selectedDbType !== 'mongodb' || !useConnectionString) && (
            <>
              <Form.Item
                label="主机地址"
                name="host"
                rules={[{ required: true, message: '请输入主机地址' }]}
              >
                <Input placeholder="localhost 或 IP地址" />
              </Form.Item>

              <Form.Item
                label="端口"
                name="port"
              >
                <Input 
                  type="number" 
                  placeholder={
                    selectedDbType === 'mongodb' ? '27017' :
                    selectedDbType === 'mysql' ? '3306' :
                    selectedDbType === 'postgresql' ? '5432' :
                    selectedDbType === 'redis' ? '6379' :
                    '端口号'
                  }
                />
              </Form.Item>

              <Form.Item
                label="用户名"
                name="username"
              >
                <Input placeholder="数据库用户名" />
              </Form.Item>

              <Form.Item
                label="密码"
                name="password"
                extra={editingConfig ? "留空表示不修改密码" : "密码将加密存储"}
              >
                <Input.Password placeholder={editingConfig ? "留空表示不修改" : "数据库密码"} />
              </Form.Item>

              {selectedDbType !== 'redis' && (
                <Form.Item
                  label={selectedDbType === 'redis' ? '数据库索引' : '数据库名'}
                  name="database"
                >
                  <Input placeholder={selectedDbType === 'redis' ? '0' : '数据库名称'} />
                </Form.Item>
              )}
            </>
          )}

          {/* MongoDB主机连接方式的额外字段 */}
          {selectedDbType === 'mongodb' && !useConnectionString && (
            <>
              <Form.Item
                label="副本集名称"
                name="replica_set"
                extra="MongoDB副本集名称（可选）"
              >
                <Input placeholder="rs0" />
              </Form.Item>

              <Form.Item
                label="认证数据库"
                name="auth_source"
                extra="MongoDB认证数据库（可选）"
              >
                <Input placeholder="admin" />
              </Form.Item>
            </>
          )}

          <Form.Item
            label="描述"
            name="description"
          >
            <TextArea rows={3} placeholder="配置说明" />
          </Form.Item>

          <Form.Item
            label="状态"
            name="is_active"
            valuePropName="checked"
          >
            <Select>
              <Option value={true}>启用</Option>
              <Option value={false}>禁用</Option>
            </Select>
          </Form.Item>

          <Form.Item
            label="权限"
            name="is_public"
            valuePropName="checked"
            tooltip="公开配置所有用户可见，私有配置仅创建者和管理员可见"
          >
            <Switch checkedChildren="公开" unCheckedChildren="私有" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DatabaseConfig;
