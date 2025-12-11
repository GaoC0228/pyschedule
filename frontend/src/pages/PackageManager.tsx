import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Input,
  Button,
  Space,
  message,
  Modal,
  Form,
  Tag,
  Popconfirm,
  Alert
} from 'antd';
import {
  SearchOutlined,
  PlusOutlined,
  DeleteOutlined,
  ReloadOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import api from '../api/axios';

const { Search, TextArea } = Input;

interface Package {
  name: string;
  version: string;
}

const PackageManager: React.FC = () => {
  const [filteredPackages, setFilteredPackages] = useState<Package[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [installModalVisible, setInstallModalVisible] = useState(false);
  const [batchInstallModalVisible, setBatchInstallModalVisible] = useState(false);
  const [installForm] = Form.useForm();
  const [batchForm] = Form.useForm();
  const [installing, setInstalling] = useState(false);

  // 加载已安装的包
  const loadPackages = async (search = '') => {
    setLoading(true);
    try {
      const response = await api.get('/packages/installed', {
        params: { search }
      });

      if (response.data.success) {
        setFilteredPackages(response.data.data);
      }
    } catch (error: any) {
      if (error.response?.status === 403) {
        message.error('您没有包管理权限');
      } else {
        message.error('加载包列表失败');
      }
      console.error('Error loading packages:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPackages();
  }, []);

  // 搜索包
  const handleSearch = (value: string) => {
    setSearchText(value);
    loadPackages(value);
  };

  // 安装单个包
  const handleInstall = async (values: any) => {
    setInstalling(true);
    try {
      const response = await api.post(
        '/packages/install',
        {
          package_name: values.package_name,
          version: values.version || null
        }
      );

      if (response.data.success) {
        message.success('安装成功！');
        installForm.resetFields();
        setInstallModalVisible(false);
        loadPackages(searchText);
      } else {
        Modal.error({
          title: '安装失败',
          content: (
            <pre style={{ maxHeight: '400px', overflow: 'auto', fontSize: '12px' }}>
              {response.data.output}
            </pre>
          ),
          width: 600
        });
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || '安装失败');
      console.error('Error installing package:', error);
    } finally {
      setInstalling(false);
    }
  };

  // 批量安装
  const handleBatchInstall = async (values: any) => {
    const packageList = values.packages
      .split('\n')
      .map((line: string) => line.trim())
      .filter((line: string) => line && !line.startsWith('#'));

    if (packageList.length === 0) {
      message.warning('请输入至少一个包');
      return;
    }

    setInstalling(true);
    try {
      const response = await api.post(
        '/packages/batch-install',
        { packages: packageList }
      );

      const { success, results } = response.data;
      const successCount = results.filter((r: any) => r.success).length;
      const failCount = results.filter((r: any) => !r.success).length;

      if (success) {
        message.success(`批量安装完成！成功: ${successCount}`);
      } else {
        Modal.warning({
          title: '批量安装完成',
          content: (
            <div>
              <p>成功: {successCount} 个，失败: {failCount} 个</p>
              <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                {results.filter((r: any) => !r.success).map((r: any, i: number) => (
                  <div key={i} style={{ marginTop: '10px' }}>
                    <strong>{r.package}</strong>
                    <pre style={{ fontSize: '11px', background: '#f5f5f5', padding: '5px' }}>
                      {r.output.substring(0, 200)}...
                    </pre>
                  </div>
                ))}
              </div>
            </div>
          ),
          width: 600
        });
      }

      batchForm.resetFields();
      setBatchInstallModalVisible(false);
      loadPackages(searchText);
    } catch (error: any) {
      message.error(error.response?.data?.detail || '批量安装失败');
      console.error('Error batch installing:', error);
    } finally {
      setInstalling(false);
    }
  };

  // 卸载包
  const handleUninstall = async (packageName: string) => {
    try {
      const response = await api.post(
        '/packages/uninstall',
        { package_name: packageName }
      );

      if (response.data.success) {
        message.success('卸载成功！');
        loadPackages(searchText);
      } else {
        message.error('卸载失败');
      }
    } catch (error: any) {
      if (error.response?.status === 400) {
        message.error(error.response.data.detail);
      } else {
        message.error('卸载失败');
      }
      console.error('Error uninstalling package:', error);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '包名',
      dataIndex: 'name',
      key: 'name',
      width: '40%',
      render: (text: string) => <strong>{text}</strong>
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: '30%',
      render: (text: string) => <Tag color="blue">{text}</Tag>
    },
    {
      title: '操作',
      key: 'action',
      width: '30%',
      render: (_: any, record: Package) => (
        <Space>
          <Popconfirm
            title="确认卸载"
            description={`确定要卸载 ${record.name} 吗？`}
            onConfirm={() => handleUninstall(record.name)}
            okText="确定"
            cancelText="取消"
          >
            <Button
              type="link"
              danger
              icon={<DeleteOutlined />}
              size="small"
            >
              卸载
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <span>📦 Python包管理</span>
            <Tag color="green">{filteredPackages.length} 个已安装包</Tag>
          </Space>
        }
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setInstallModalVisible(true)}
            >
              安装包
            </Button>
            <Button
              icon={<PlusOutlined />}
              onClick={() => setBatchInstallModalVisible(true)}
            >
              批量安装
            </Button>
            <Button icon={<ReloadOutlined />} onClick={() => loadPackages(searchText)}>
              刷新
            </Button>
          </Space>
        }
      >
        <Alert
          message="包持久化说明"
          description="所有通过此界面安装的包将自动同步到 requirements.txt，容器重建后会自动重新安装。"
          type="info"
          icon={<InfoCircleOutlined />}
          showIcon
          closable
          style={{ marginBottom: '16px' }}
        />

        <div style={{ marginBottom: '16px' }}>
          <Search
            placeholder="搜索包名..."
            allowClear
            enterButton={<SearchOutlined />}
            onSearch={handleSearch}
            style={{ width: 300 }}
          />
        </div>

        <Table
          columns={columns}
          dataSource={filteredPackages}
          rowKey="name"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 个包`
          }}
        />
      </Card>

      {/* 安装单个包对话框 */}
      <Modal
        title="安装Python包"
        open={installModalVisible}
        onCancel={() => {
          setInstallModalVisible(false);
          installForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form form={installForm} onFinish={handleInstall} layout="vertical">
          <Form.Item
            label="包名"
            name="package_name"
            rules={[{ required: true, message: '请输入包名' }]}
          >
            <Input placeholder="例如: pandas, numpy, requests" />
          </Form.Item>

          <Form.Item
            label="版本（可选）"
            name="version"
            help="留空安装最新版本"
          >
            <Input placeholder="例如: 2.0.3" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={installing}>
                安装
              </Button>
              <Button onClick={() => setInstallModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 批量安装对话框 */}
      <Modal
        title="批量安装Python包"
        open={batchInstallModalVisible}
        onCancel={() => {
          setBatchInstallModalVisible(false);
          batchForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form form={batchForm} onFinish={handleBatchInstall} layout="vertical">
          <Form.Item
            label="包列表"
            name="packages"
            rules={[{ required: true, message: '请输入包列表' }]}
            help="每行一个包，可指定版本（如 pandas==2.0.3），支持 # 注释"
          >
            <TextArea
              rows={10}
              placeholder={'pandas==2.0.3\nnumpy\nrequests>=2.28.0\n# 这是注释'}
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={installing}>
                开始安装
              </Button>
              <Button onClick={() => setBatchInstallModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PackageManager;
