import React, { useState, useEffect, useRef } from 'react';
import { 
  Card, Button, Upload, message, Space, Tag,
  Breadcrumb, Input, Typography, List, Spin, Modal, Checkbox, Dropdown 
} from 'antd';
import type { MenuProps } from 'antd';
import {
  FolderOutlined, FileOutlined, UploadOutlined, 
  PlayCircleOutlined, DeleteOutlined, PlusOutlined,
  ReloadOutlined, DownloadOutlined, ClearOutlined,
  FolderOpenOutlined, CodeOutlined, EditOutlined, FileAddOutlined,
  CodeSandboxOutlined, MoreOutlined, FullscreenOutlined, FullscreenExitOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import axios from '../api/axios';
import dayjs from 'dayjs';
import TerminalModal from '../components/TerminalModal';
import CodeEditor from '../components/CodeEditor';
import CsvViewer from '../components/CsvViewer';
import ExcelViewer from '../components/ExcelViewer';
import WordViewer from '../components/WordViewer';
import PdfViewer from '../components/PdfViewer';

const { Text } = Typography;

interface FileItem {
  name: string;
  path: string;
  type: 'file' | 'directory';
  size: number;
  modified: string;
  extension?: string;
}

const Workspace: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [currentPath, setCurrentPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [consoleOutput, setConsoleOutput] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string>('');
  const [createDirVisible, setCreateDirVisible] = useState(false);
  const [newDirName, setNewDirName] = useState('');
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingFile, setEditingFile] = useState<{ path: string; name: string; content: string } | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [saving, setSaving] = useState(false);
  const [selectedItems, setSelectedItems] = useState<string[]>([]);
  const [terminalVisible, setTerminalVisible] = useState(false);
  const [terminalScript, setTerminalScript] = useState<{ path: string; name: string } | null>(null);
  const [renamingItem, setRenamingItem] = useState<{ path: string; name: string } | null>(null);
  const [newName, setNewName] = useState('');
  const [createFileVisible, setCreateFileVisible] = useState(false);
  const [newFileName, setNewFileName] = useState('');
  const [consoleFullscreen, setConsoleFullscreen] = useState(false);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [excelViewerVisible, setExcelViewerVisible] = useState(false);
  const [excelViewerFile, setExcelViewerFile] = useState<{ path: string; name: string } | null>(null);
  const [wordViewerVisible, setWordViewerVisible] = useState(false);
  const [wordViewerFile, setWordViewerFile] = useState<{ path: string; name: string } | null>(null);
  const [pdfViewerVisible, setPdfViewerVisible] = useState(false);
  const [pdfViewerFile, setPdfViewerFile] = useState<{ path: string; name: string } | null>(null);
  const consoleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadFiles();
  }, [currentPath]);

  useEffect(() => {
    // 自动滚动到底部
    if (consoleRef.current) {
      consoleRef.current.scrollTop = consoleRef.current.scrollHeight;
    }
  }, [consoleOutput]);

  const addConsoleLog = (text: string, type: 'info' | 'success' | 'error' | 'warning' = 'info') => {
    const timestamp = dayjs().format('HH:mm:ss');
    const colorMap = {
      info: '#00ff00',
      success: '#00ff00',
      error: '#ff0000',
      warning: '#ffff00'
    };
    setConsoleOutput(prev => [...prev, `[${timestamp}] ${text}`]);
  };

  const clearConsole = () => {
    setConsoleOutput([]);
    addConsoleLog('控制台已清空', 'info');
  };

  const loadFiles = async () => {
    setLoading(true);
    addConsoleLog(`加载目录: ${currentPath || '根目录'}`, 'info');
    try {
      const response = await axios.get('/workspace/files', {
        params: { path: currentPath }
      });
      setFiles(response.data.items);
      setSelectedItems([]); // 清空选择
      addConsoleLog(`✓ 找到 ${response.data.items.length} 个项目`, 'success');
    } catch (error: any) {
      const errorMsg = '加载文件列表失败: ' + (error.response?.data?.detail || error.message);
      message.error(errorMsg);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFileClick = (record: FileItem) => {
    if (record.type === 'directory') {
      setCurrentPath(record.path);
      addConsoleLog(`进入目录: ${record.name}`, 'info');
    }
  };

  const handleBreadcrumbClick = (path: string) => {
    setCurrentPath(path);
    addConsoleLog(`返回: ${path || '根目录'}`, 'info');
  };

  const handleUpload = async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    addConsoleLog(`开始上传: ${file.name}`, 'info');
    try {
      await axios.post('/workspace/upload', formData, {
        params: { path: currentPath },
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      message.success('文件上传成功');
      addConsoleLog(`✓ 上传成功: ${file.name}`, 'success');
      loadFiles();
    } catch (error: any) {
      const errorMsg = '上传失败: ' + (error.response?.data?.detail || error.message);
      message.error(errorMsg);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
    }
    
    return false;
  };

  const handleExecute = async (filePath: string, fileName: string) => {
    setSelectedFile(filePath);
    setExecuting(true);
    
    addConsoleLog('='.repeat(60), 'info');
    addConsoleLog(`准备执行脚本: ${fileName}`, 'info');
    addConsoleLog(`文件路径: ${filePath}`, 'info');
    addConsoleLog('='.repeat(60), 'info');

    try {
      // 先分析脚本安全性
      addConsoleLog('正在分析脚本安全性...', 'warning');
      const analysisResponse = await axios.post('/workspace/analyze-script', null, {
        params: { file_path: filePath }
      });
      
      const analysis = analysisResponse.data;
      
      // 如果有风险，显示确认对话框
      if (analysis.has_risk) {
        addConsoleLog('', 'info');
        addConsoleLog('⚠️ 检测到脚本风险！', 'warning');
        addConsoleLog(`风险等级: ${analysis.risk_level.toUpperCase()}`, 'warning');
        
        // 显示数据库配置信息
        if (analysis.database_configs && analysis.database_configs.length > 0) {
          addConsoleLog('', 'info');
          addConsoleLog('将连接以下数据库:', 'info');
          analysis.database_configs.forEach((db: any) => {
            addConsoleLog(`  - ${db.display_name} (${db.environment}) - ${db.db_type}`, 
              db.environment === 'production' ? 'error' : 'info');
          });
        }
        
        // 显示危险操作
        if (analysis.dangerous_operations && analysis.dangerous_operations.length > 0) {
          addConsoleLog('', 'info');
          addConsoleLog('检测到以下操作:', 'warning');
          analysis.dangerous_operations.forEach((op: string) => {
            addConsoleLog(`  - ${op}`, 'warning');
          });
        }
        
        addConsoleLog('', 'info');
        
        // 显示确认对话框
        const confirmed = await new Promise<boolean>((resolve) => {
          Modal.confirm({
            title: '⚠️ 脚本执行风险提示',
            width: 700,
            icon: <ExclamationCircleOutlined style={{ color: analysis.risk_level === 'critical' ? '#ff4d4f' : '#faad14' }} />,
            content: (
              <div>
                <p style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 16 }}>
                  风险等级: <span style={{ color: analysis.risk_level === 'critical' ? '#ff4d4f' : '#faad14' }}>
                    {analysis.risk_level.toUpperCase()}
                  </span>
                </p>
                
                {analysis.database_configs && analysis.database_configs.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <p style={{ fontWeight: 'bold', marginBottom: 8 }}>将连接以下数据库：</p>
                    {analysis.database_configs.map((db: any, index: number) => (
                      <div key={index} style={{ 
                        padding: 8, 
                        background: db.environment === 'production' ? '#fff2e8' : '#f0f0f0',
                        borderLeft: `3px solid ${db.environment === 'production' ? '#ff4d4f' : '#1890ff'}`,
                        marginBottom: 8
                      }}>
                        <div><strong>{db.display_name}</strong></div>
                        <div>环境: <Tag color={db.environment === 'production' ? 'red' : 'blue'}>{db.environment}</Tag></div>
                        <div>类型: {db.db_type}</div>
                        <div>主机: {db.host}</div>
                      </div>
                    ))}
                  </div>
                )}
                
                {analysis.dangerous_operations && analysis.dangerous_operations.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    <p style={{ fontWeight: 'bold', marginBottom: 8 }}>检测到以下操作：</p>
                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                      {analysis.dangerous_operations.map((op: string, index: number) => (
                        <Tag key={index} color="warning">{op}</Tag>
                      ))}
                    </div>
                  </div>
                )}
                
                {analysis.warnings && analysis.warnings.length > 0 && (
                  <div style={{ marginBottom: 16 }}>
                    {analysis.warnings.map((warning: string, index: number) => (
                      <div key={index} style={{ color: '#ff4d4f', marginBottom: 4 }}>
                        {warning}
                      </div>
                    ))}
                  </div>
                )}
                
                <p style={{ marginTop: 16, fontWeight: 'bold' }}>
                  {analysis.risk_level === 'critical' 
                    ? '🚨 强烈建议您仔细检查脚本代码，确认无误后再执行！' 
                    : '请确认是否继续执行此脚本？'}
                </p>
              </div>
            ),
            okText: '确认执行',
            okType: analysis.risk_level === 'critical' ? 'danger' : 'primary',
            cancelText: '取消',
            onOk: () => resolve(true),
            onCancel: () => resolve(false)
          });
        });
        
        if (!confirmed) {
          addConsoleLog('用户取消执行', 'warning');
          addConsoleLog('='.repeat(60), 'info');
          setExecuting(false);
          return;
        }
      }
      
      addConsoleLog('', 'info');
      addConsoleLog('开始执行脚本...', 'warning');
      
      const response = await axios.post('/workspace/execute', null, {
        params: { file_path: filePath }
      });

      const scriptDir = filePath.substring(0, filePath.lastIndexOf('/')) || '根目录';
      
      addConsoleLog('', 'info');
      addConsoleLog(`执行用户: ${response.data.executed_by}`, 'info');
      addConsoleLog(`执行时间: ${dayjs(response.data.executed_at).format('YYYY-MM-DD HH:mm:ss')}`, 'info');
      addConsoleLog(`工作目录: ${scriptDir}`, 'info');
      addConsoleLog(`返回码: ${response.data.returncode}`, 'info');
      addConsoleLog(`状态: ${response.data.success ? '✓ 成功' : '✗ 失败'}`, response.data.success ? 'success' : 'error');
      addConsoleLog('', 'info');
      addConsoleLog('=== 标准输出 ===', 'info');
      
      if (response.data.stdout) {
        response.data.stdout.split('\n').forEach((line: string) => {
          addConsoleLog(line, 'info');
        });
      } else {
        addConsoleLog('(无输出)', 'info');
      }
      
      if (response.data.stderr) {
        addConsoleLog('', 'info');
        addConsoleLog('=== 错误输出 ===', 'warning');
        response.data.stderr.split('\n').forEach((line: string) => {
          addConsoleLog(line, 'error');
        });
      }
      
      addConsoleLog('', 'info');
      addConsoleLog('='.repeat(60), 'info');
      addConsoleLog('执行完成！', 'success');
      addConsoleLog('提示: 如有文件生成，请点击刷新查看', 'info');
      addConsoleLog('='.repeat(60), 'info');
      
      if (response.data.success) {
        message.success('脚本执行成功！');
        // 自动刷新文件列表
        setTimeout(() => loadFiles(), 1000);
      }
    } catch (error: any) {
      const errorMsg = '执行失败: ' + (error.response?.data?.detail || error.message);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
      message.error(errorMsg);
    } finally {
      setExecuting(false);
    }
  };

  const handleToggleSelect = (filePath: string) => {
    setSelectedItems(prev => {
      if (prev.includes(filePath)) {
        return prev.filter(p => p !== filePath);
      } else {
        return [...prev, filePath];
      }
    });
  };

  const handleSelectAll = () => {
    if (selectedItems.length === files.length) {
      setSelectedItems([]);
    } else {
      setSelectedItems(files.map(f => f.path));
    }
  };

  const handleBatchDelete = async () => {
    if (selectedItems.length === 0) {
      message.warning('请先选择要删除的文件');
      return;
    }

    Modal.confirm({
      title: '批量删除确认',
      content: `确定要删除选中的 ${selectedItems.length} 个项目吗？`,
      okText: '确定',
      cancelText: '取消',
      okType: 'danger',
      onOk: async () => {
        addConsoleLog(`批量删除 ${selectedItems.length} 个项目`, 'warning');
        let successCount = 0;
        let failCount = 0;

        for (const filePath of selectedItems) {
          try {
            await axios.delete('/workspace/delete', {
              params: { file_path: filePath }
            });
            successCount++;
            addConsoleLog(`✓ 已删除: ${filePath}`, 'success');
          } catch (error: any) {
            failCount++;
            addConsoleLog(`✗ 删除失败: ${filePath}`, 'error');
          }
        }

        message.success(`删除完成：成功 ${successCount} 个，失败 ${failCount} 个`);
        setSelectedItems([]);
        loadFiles();
      }
    });
  };

  const handleCreateDir = async () => {
    if (!newDirName.trim()) {
      message.error('请输入目录名称');
      return;
    }

    const dirPath = currentPath ? `${currentPath}/${newDirName}` : newDirName;
    addConsoleLog(`创建目录: ${newDirName}`, 'info');

    try {
      await axios.post('/workspace/mkdir', null, {
        params: { dir_path: dirPath }
      });
      message.success('目录创建成功');
      addConsoleLog(`✓ 目录已创建: ${newDirName}`, 'success');
      setCreateDirVisible(false);
      setNewDirName('');
      loadFiles();
    } catch (error: any) {
      const errorMsg = '创建目录失败: ' + (error.response?.data?.detail || error.message);
      message.error(errorMsg);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
    }
  };

  const handleRename = async () => {
    if (!renamingItem || !newName.trim()) {
      message.error('请输入新名称');
      return;
    }

    if (newName === renamingItem.name) {
      setRenamingItem(null);
      setNewName('');
      return;
    }

    const oldPath = renamingItem.path;
    const newPath = currentPath ? `${currentPath}/${newName}` : newName;
    
    addConsoleLog(`重命名: ${renamingItem.name} → ${newName}`, 'info');

    try {
      await axios.post('/workspace/rename', null, {
        params: { 
          old_path: oldPath,
          new_path: newPath
        }
      });
      message.success('重命名成功');
      addConsoleLog(`✓ 已重命名: ${renamingItem.name} → ${newName}`, 'success');
      setRenamingItem(null);
      setNewName('');
      loadFiles();
    } catch (error: any) {
      const errorMsg = '重命名失败: ' + (error.response?.data?.detail || error.message);
      message.error(errorMsg);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
    }
  };

  const downloadConsoleLog = () => {
    const logContent = consoleOutput.join('\n');
    const blob = new Blob([logContent], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `console_log_${dayjs().format('YYYYMMDDHHmmss')}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addConsoleLog('✓ 日志已下载', 'success');
  };

  const downloadFile = async (filePath: string, fileName: string) => {
    addConsoleLog(`下载文件: ${fileName}`, 'info');
    try {
      const response = await axios.get('/workspace/download', {
        params: { file_path: filePath },
        responseType: 'blob'
      });
      
      const url = URL.createObjectURL(response.data);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      message.success('文件下载成功');
      addConsoleLog(`✓ 已下载: ${fileName}`, 'success');
    } catch (error: any) {
      const errorMsg = '下载失败: ' + (error.response?.data?.detail || error.message);
      message.error(errorMsg);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
    }
  };

  const handleEditFile = async (filePath: string, fileName: string) => {
    const fileExt = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
    
    // Excel文件：打开Excel查看器
    if (['.xls', '.xlsx', '.xlsm', '.xlsb'].includes(fileExt)) {
      setExcelViewerFile({ path: filePath, name: fileName });
      setExcelViewerVisible(true);
      addConsoleLog(`打开Excel查看器: ${fileName}`, 'info');
      return;
    }
    
    // Word文档：打开Word查看器
    if (['.doc', '.docx'].includes(fileExt)) {
      setWordViewerFile({ path: filePath, name: fileName });
      setWordViewerVisible(true);
      addConsoleLog(`打开Word查看器: ${fileName}`, 'info');
      return;
    }
    
    // PDF文档：打开PDF查看器
    if (['.pdf'].includes(fileExt)) {
      setPdfViewerFile({ path: filePath, name: fileName });
      setPdfViewerVisible(true);
      addConsoleLog(`打开PDF查看器: ${fileName}`, 'info');
      return;
    }
    
    // 检查文件类型是否支持编辑
    const editableExtensions = [
      '.py', '.txt', '.md', '.json', '.xml', '.yml', '.yaml', 
      '.sh', '.conf', '.cfg', '.ini', '.log', '.csv',
      '.js', '.ts', '.tsx', '.jsx', '.css', '.scss', '.html',
      '.java', '.c', '.cpp', '.h', '.go', '.rs', '.sql'
    ];
    
    if (!editableExtensions.includes(fileExt)) {
      // 根据文件类型提供友好的提示
      let fileTypeDesc = '二进制文件或不支持的格式';
      let suggestedApp = '本地程序';
      
      if (['.ppt', '.pptx'].includes(fileExt)) {
        fileTypeDesc = 'PowerPoint演示文稿';
        suggestedApp = 'Microsoft PowerPoint 或 WPS演示';
      } else if (['.zip', '.rar', '.7z', '.tar', '.gz'].includes(fileExt)) {
        fileTypeDesc = '压缩文件';
        suggestedApp = '解压软件';
      } else if (['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'].includes(fileExt)) {
        fileTypeDesc = '图片文件';
        suggestedApp = '图片查看器';
      } else if (['.exe', '.dll', '.so', '.dylib'].includes(fileExt)) {
        fileTypeDesc = '可执行文件或库文件';
        suggestedApp = '相应的执行环境';
      }
      
      Modal.confirm({
        title: '不支持在线查看',
        icon: <ExclamationCircleOutlined />,
        content: (
          <div>
            <p>文件 <strong>"{fileName}"</strong> 是{fileTypeDesc}，暂不支持在线查看。</p>
            <p>建议下载后使用 <strong>{suggestedApp}</strong> 打开。</p>
          </div>
        ),
        okText: '下载文件',
        cancelText: '取消',
        onOk: () => downloadFile(filePath, fileName)
      });
      return;
    }
    
    addConsoleLog(`打开编辑: ${fileName}`, 'info');
    try {
      const response = await axios.get('/workspace/read', {
        params: { file_path: filePath }
      });
      
      setEditingFile({ path: filePath, name: fileName, content: response.data.content });
      setFileContent(response.data.content);
      setEditModalVisible(true);
      addConsoleLog(`✓ 文件已加载`, 'success');
    } catch (error: any) {
      const errorMsg = '读取文件失败: ' + (error.response?.data?.detail || error.message);
      message.error(errorMsg);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
    }
  };

  const handleSaveFile = async () => {
    if (!editingFile) return;
    
    setSaving(true);
    addConsoleLog(`保存文件: ${editingFile.name}`, 'info');
    
    try {
      await axios.put('/workspace/update', {
        file_path: editingFile.path,
        content: fileContent
      });
      
      message.success('文件保存成功');
      addConsoleLog(`✓ 已保存: ${editingFile.name}`, 'success');
      setEditModalVisible(false);
      setEditingFile(null);
      loadFiles();
    } catch (error: any) {
      const errorMsg = '保存失败: ' + (error.response?.data?.detail || error.message);
      message.error(errorMsg);
      addConsoleLog(`✗ ${errorMsg}`, 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleCreateNewFile = () => {
    setNewFileName('new_script.py');
    setCreateFileVisible(true);
  };

  const handleConfirmCreateFile = () => {
    if (!newFileName.trim()) {
      message.error('请输入文件名');
      return;
    }

    // 确保文件名以.py结尾
    let fileName = newFileName.trim();
    if (!fileName.endsWith('.py')) {
      fileName += '.py';
    }

    const filePath = currentPath ? `${currentPath}/${fileName}` : fileName;
    const defaultContent = `#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
${fileName.replace('.py', '')}
"""

print("Hello, World!")
`;
    
    setEditingFile({ path: filePath, name: fileName, content: defaultContent });
    setFileContent(defaultContent);
    setEditModalVisible(true);
    setCreateFileVisible(false);
    setNewFileName('');
    addConsoleLog(`创建新文件: ${fileName}`, 'info');
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return '-';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getBreadcrumbs = () => {
    if (!currentPath) return [{ path: '', name: '根目录' }];
    
    const parts = currentPath.split('/');
    const breadcrumbs = [{ path: '', name: '根目录' }];
    
    let accumulated = '';
    parts.forEach(part => {
      accumulated = accumulated ? `${accumulated}/${part}` : part;
      breadcrumbs.push({ path: accumulated, name: part });
    });
    
    return breadcrumbs;
  };

  // 过滤文件列表
  const filteredFiles = files.filter(file => {
    if (!searchKeyword.trim()) return true;
    const keyword = searchKeyword.toLowerCase();
    // 支持文件名和路径搜索
    return file.name.toLowerCase().includes(keyword) || 
           file.path.toLowerCase().includes(keyword);
  });

  return (
    <div style={{ height: 'calc(100vh - 120px)' }}>
      <PanelGroup direction="horizontal" style={{ height: '100%' }}>
        {/* 左侧文件浏览器 */}
        <Panel defaultSize={40} minSize={20}>
          <Card
            title={
              <Space>
                <FolderOpenOutlined />
                <span>文件浏览器</span>
              </Space>
            }
            extra={
              <Space>
                <Button
                  size="small"
                  type="primary"
                  icon={<FileAddOutlined />}
                  onClick={handleCreateNewFile}
                >
                  新建文件
                </Button>
                <Button
                  size="small"
                  icon={<PlusOutlined />}
                  onClick={() => setCreateDirVisible(true)}
                >
                  新建目录
                </Button>
                <Upload
                  beforeUpload={handleUpload}
                  showUploadList={false}
                >
                  <Button size="small" icon={<UploadOutlined />}>上传</Button>
                </Upload>
                <Button size="small" icon={<ReloadOutlined />} onClick={loadFiles}>
                  刷新
                </Button>
              </Space>
            }
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, overflow: 'auto', padding: '16px' }}
          >
            <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
              <Breadcrumb>
                {getBreadcrumbs().map((item, index) => (
                  <Breadcrumb.Item key={index}>
                    <a onClick={() => handleBreadcrumbClick(item.path)}>
                      {item.name}
                    </a>
                  </Breadcrumb.Item>
                ))}
              </Breadcrumb>
              
              {/* 文件搜索框 */}
              <Input.Search
                placeholder="搜索文件或文件夹..."
                allowClear
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                style={{ width: '100%' }}
                prefix={<FolderOpenOutlined style={{ color: '#999' }} />}
              />
              
              {files.length > 0 && (
                <Space>
                  <Checkbox
                    checked={selectedItems.length === files.length && files.length > 0}
                    indeterminate={selectedItems.length > 0 && selectedItems.length < files.length}
                    onChange={handleSelectAll}
                  >
                    全选
                  </Checkbox>
                  {selectedItems.length > 0 && (
                    <Button
                      danger
                      size="small"
                      icon={<DeleteOutlined />}
                      onClick={handleBatchDelete}
                    >
                      删除选中 ({selectedItems.length})
                    </Button>
                  )}
                </Space>
              )}
            </Space>

            <Spin spinning={loading}>
              <List
                dataSource={filteredFiles}
                renderItem={(item) => (
                  <List.Item
                    key={item.path}
                    style={{
                      padding: '12px',
                      cursor: item.type === 'directory' ? 'pointer' : 'default',
                      borderRadius: '4px',
                      marginBottom: '4px',
                      background: selectedFile === item.path ? '#e6f7ff' : 'transparent'
                    }}
                    onMouseEnter={(e) => {
                      if (item.type === 'directory') {
                        e.currentTarget.style.background = '#f5f5f5';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (selectedFile !== item.path) {
                        e.currentTarget.style.background = 'transparent';
                      }
                    }}
                    onClick={() => item.type === 'directory' && handleFileClick(item)}
                    actions={[
                      item.type === 'file' && item.extension === '.py' && (
                        <Button
                          type="primary"
                          size="small"
                          icon={<PlayCircleOutlined />}
                          onClick={(e) => {
                            e.stopPropagation();
                            handleExecute(item.path, item.name);
                          }}
                          loading={executing && selectedFile === item.path}
                        >
                          执行
                        </Button>
                      ),
                      item.type === 'file' && item.extension === '.py' && (
                        <Button
                          size="small"
                          icon={<CodeSandboxOutlined />}
                          onClick={async (e) => {
                            e.stopPropagation();
                            addConsoleLog('='.repeat(60), 'info');
                            addConsoleLog(`准备启动交互式执行: ${item.name}`, 'info');
                            addConsoleLog('='.repeat(60), 'info');
                            
                            try {
                              // 先分析脚本安全性
                              addConsoleLog('正在分析脚本安全性...', 'warning');
                              const analysisResponse = await axios.post('/workspace/analyze-script', null, {
                                params: { file_path: item.path }
                              });
                              
                              const analysis = analysisResponse.data;
                              
                              // 如果有风险，显示确认对话框
                              if (analysis.has_risk) {
                                addConsoleLog('', 'info');
                                addConsoleLog('⚠️ 检测到脚本风险！', 'warning');
                                
                                const confirmed = await new Promise<boolean>((resolve) => {
                                  Modal.confirm({
                                    title: '⚠️ 交互式执行风险提示',
                                    width: 700,
                                    icon: <ExclamationCircleOutlined style={{ color: analysis.risk_level === 'critical' ? '#ff4d4f' : '#faad14' }} />,
                                    content: (
                                      <div>
                                        <p style={{ fontSize: 16, fontWeight: 'bold', marginBottom: 16 }}>
                                          风险等级: <span style={{ color: analysis.risk_level === 'critical' ? '#ff4d4f' : '#faad14' }}>
                                            {analysis.risk_level.toUpperCase()}
                                          </span>
                                        </p>
                                        
                                        {analysis.database_configs && analysis.database_configs.length > 0 && (
                                          <div style={{ marginBottom: 16 }}>
                                            <p style={{ fontWeight: 'bold', marginBottom: 8 }}>将连接以下数据库：</p>
                                            {analysis.database_configs.map((db: any, index: number) => (
                                              <div key={index} style={{ 
                                                padding: 8, 
                                                background: db.environment === 'production' ? '#fff2e8' : '#f0f0f0',
                                                borderLeft: `3px solid ${db.environment === 'production' ? '#ff4d4f' : '#1890ff'}`,
                                                marginBottom: 8
                                              }}>
                                                <div><strong>{db.display_name}</strong></div>
                                                <div>环境: <Tag color={db.environment === 'production' ? 'red' : 'blue'}>{db.environment}</Tag></div>
                                                <div>类型: {db.db_type}</div>
                                                <div>主机: {db.host}</div>
                                              </div>
                                            ))}
                                          </div>
                                        )}
                                        
                                        {analysis.dangerous_operations && analysis.dangerous_operations.length > 0 && (
                                          <div style={{ marginBottom: 16 }}>
                                            <p style={{ fontWeight: 'bold', marginBottom: 8 }}>检测到以下操作：</p>
                                            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                              {analysis.dangerous_operations.map((op: string, index: number) => (
                                                <Tag key={index} color="warning">{op}</Tag>
                                              ))}
                                            </div>
                                          </div>
                                        )}
                                        
                                        <p style={{ marginTop: 16, fontWeight: 'bold' }}>
                                          请确认是否在交互式终端中执行此脚本？
                                        </p>
                                      </div>
                                    ),
                                    okText: '确认执行',
                                    okType: analysis.risk_level === 'critical' ? 'danger' : 'primary',
                                    cancelText: '取消',
                                    onOk: () => resolve(true),
                                    onCancel: () => resolve(false)
                                  });
                                });
                                
                                if (!confirmed) {
                                  addConsoleLog('用户取消执行', 'warning');
                                  addConsoleLog('='.repeat(60), 'info');
                                  return;
                                }
                              }
                              
                              addConsoleLog('', 'info');
                              addConsoleLog('启动交互式终端...', 'info');
                              addConsoleLog('提示: 交互式终端将在新窗口打开，所有输出会同步记录到日志', 'info');
                              addConsoleLog('='.repeat(60), 'info');
                              setTerminalScript({ path: item.path, name: item.name });
                              setTerminalVisible(true);
                              
                            } catch (error: any) {
                              addConsoleLog('分析脚本失败: ' + (error.response?.data?.detail || error.message), 'error');
                              addConsoleLog('='.repeat(60), 'info');
                            }
                          }}
                        >
                          交互式
                        </Button>
                      ),
                      <Dropdown
                        key="more"
                        menu={{
                          items: [
                            item.type === 'file' && {
                              key: 'edit',
                              icon: <EditOutlined />,
                              label: '编辑',
                              onClick: () => handleEditFile(item.path, item.name)
                            },
                            item.type === 'file' && {
                              key: 'download',
                              icon: <DownloadOutlined />,
                              label: '下载',
                              onClick: () => downloadFile(item.path, item.name)
                            },
                            {
                              key: 'rename',
                              icon: <EditOutlined />,
                              label: '重命名',
                              onClick: () => {
                                setRenamingItem({ path: item.path, name: item.name });
                                setNewName(item.name);
                              }
                            }
                          ].filter(Boolean) as MenuProps['items']
                        }}
                        trigger={['click']}
                      >
                        <Button
                          size="small"
                          icon={<MoreOutlined />}
                          onClick={(e) => e.stopPropagation()}
                        >
                          更多
                        </Button>
                      </Dropdown>
                    ].filter(Boolean)}
                  >
                    <List.Item.Meta
                      avatar={
                        <Space>
                          <Checkbox
                            checked={selectedItems.includes(item.path)}
                            onChange={(e) => {
                              e.stopPropagation();
                              handleToggleSelect(item.path);
                            }}
                            onClick={(e) => e.stopPropagation()}
                          />
                          {item.type === 'directory' ? (
                            <FolderOutlined style={{ 
                              fontSize: 32, 
                              color: '#faad14',
                              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))'
                            }} />
                          ) : (
                            <FileOutlined style={{ 
                              fontSize: 28,
                              color: item.extension === '.py' ? '#52c41a' : 
                                     item.extension === '.csv' ? '#1890ff' :
                                     item.extension === '.sh' ? '#722ed1' :
                                     item.extension === '.json' ? '#fa8c16' :
                                     item.extension === '.md' ? '#13c2c2' :
                                     '#8c8c8c',
                              filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))'
                            }} />
                          )}
                        </Space>
                      }
                      title={
                        <div onDoubleClick={(e) => {
                          e.stopPropagation();
                          if (item.type === 'file') {
                            handleEditFile(item.path, item.name);
                          }
                        }}>
                          <Text strong={item.type === 'directory'}>{item.name}</Text>
                        </div>
                      }
                      description={
                        <Space size="large">
                          <Text type="secondary">{formatSize(item.size)}</Text>
                          <Text type="secondary">{dayjs(item.modified).format('YYYY-MM-DD HH:mm')}</Text>
                        </Space>
                      }
                    />
                  </List.Item>
                )}
              />
            </Spin>
          </Card>
        </Panel>

        {/* 拖拽分隔条 */}
        <PanelResizeHandle style={{
          width: '4px',
          background: '#d9d9d9',
          cursor: 'col-resize',
          transition: 'background 0.2s'
        }} />

        {/* 右侧控制台 */}
        <Panel defaultSize={60} minSize={30}>
          <Card
            title={
              <Space>
                <CodeOutlined />
                <span>控制台输出</span>
                {executing && <Spin size="small" />}
              </Space>
            }
            extra={
              <Space>
                <Button
                  size="small"
                  icon={consoleFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
                  onClick={() => setConsoleFullscreen(!consoleFullscreen)}
                  title={consoleFullscreen ? "退出全屏" : "全屏查看"}
                >
                  {consoleFullscreen ? "退出全屏" : "全屏"}
                </Button>
                <Button
                  size="small"
                  icon={<DownloadOutlined />}
                  onClick={downloadConsoleLog}
                  disabled={consoleOutput.length === 0}
                >
                  下载日志
                </Button>
                <Button
                  size="small"
                  icon={<ClearOutlined />}
                  onClick={clearConsole}
                >
                  清空
                </Button>
              </Space>
            }
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            bodyStyle={{ flex: 1, overflow: 'hidden', padding: 0 }}
          >
            <div
              ref={consoleRef}
              style={{
                height: '100%',
                background: '#000',
                color: '#00ff00',
                padding: '16px',
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                fontSize: '13px',
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-all'
              }}
            >
              {consoleOutput.length === 0 ? (
                <Text style={{ color: '#666' }}>
                  等待执行脚本...
                  <br /><br />
                  提示：
                  <br />• 点击"执行"按钮 - 普通模式，查看输出
                  <br />• 点击"交互式"按钮 - 弹窗终端，支持输入
                  <br />• 交互式终端的输出会同步记录到日志
                  <br />• 可以下载日志或清空控制台
                </Text>
              ) : (
                consoleOutput.map((line, index) => (
                  <div key={index}>{line}</div>
                ))
              )}
            </div>
          </Card>
        </Panel>
      </PanelGroup>

      {/* 控制台全屏Modal */}
      <Modal
        title={
          <Space>
            <CodeOutlined />
            <span>控制台输出（全屏）</span>
            {executing && <Spin size="small" />}
          </Space>
        }
        open={consoleFullscreen}
        onCancel={() => setConsoleFullscreen(false)}
        width="95%"
        style={{ top: 20 }}
        footer={[
          <Button key="download" icon={<DownloadOutlined />} onClick={downloadConsoleLog} disabled={consoleOutput.length === 0}>
            下载日志
          </Button>,
          <Button key="clear" icon={<ClearOutlined />} onClick={clearConsole}>
            清空
          </Button>,
          <Button key="close" type="primary" onClick={() => setConsoleFullscreen(false)}>
            关闭
          </Button>
        ]}
      >
        <div
          ref={consoleRef}
          style={{
            height: 'calc(100vh - 250px)',
            background: '#000',
            color: '#00ff00',
            padding: '16px',
            fontFamily: 'Consolas, Monaco, "Courier New", monospace',
            fontSize: '13px',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all'
          }}
        >
          {consoleOutput.length === 0 ? (
            <Text style={{ color: '#666' }}>
              等待执行脚本...
            </Text>
          ) : (
            consoleOutput.map((line, index) => (
              <div key={index}>{line}</div>
            ))
          )}
        </div>
      </Modal>

      {/* 新建文件对话框 */}
      <Modal
        title="新建文件"
        open={createFileVisible}
        onOk={handleConfirmCreateFile}
        onCancel={() => {
          setCreateFileVisible(false);
          setNewFileName('');
        }}
        okText="创建"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text type="secondary">请输入文件名（自动添加.py后缀）</Text>
          <Input
            placeholder="例如: my_script"
            value={newFileName}
            onChange={(e) => setNewFileName(e.target.value)}
            onPressEnter={handleConfirmCreateFile}
            autoFocus
            suffix=".py"
          />
        </Space>
      </Modal>

      {/* 创建目录对话框 */}
      <Modal
        title="创建目录"
        open={createDirVisible}
        onOk={handleCreateDir}
        onCancel={() => {
          setCreateDirVisible(false);
          setNewDirName('');
        }}
        okText="创建"
        cancelText="取消"
      >
        <Input
          placeholder="请输入目录名称"
          value={newDirName}
          onChange={(e) => setNewDirName(e.target.value)}
          onPressEnter={handleCreateDir}
          autoFocus
        />
      </Modal>

      {/* 重命名对话框 */}
      <Modal
        title="重命名"
        open={!!renamingItem}
        onOk={handleRename}
        onCancel={() => {
          setRenamingItem(null);
          setNewName('');
        }}
        okText="确定"
        cancelText="取消"
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text type="secondary">原名称: {renamingItem?.name}</Text>
          <Input
            placeholder="请输入新名称"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onPressEnter={handleRename}
            autoFocus
          />
        </Space>
      </Modal>

      {/* 文件编辑器 */}
      <Modal
        title={
          <Space>
            <EditOutlined />
            <span>{editingFile ? `编辑: ${editingFile.name}` : '新建文件'}</span>
            {editingFile && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                ({editingFile.name.split('.').pop()?.toUpperCase()} 文件)
              </Text>
            )}
          </Space>
        }
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingFile(null);
        }}
        width="80%"
        style={{ top: 20 }}
        footer={
          editingFile?.name.toLowerCase().endsWith('.csv') ? [
            <Button key="close" onClick={() => {
              setEditModalVisible(false);
              setEditingFile(null);
            }}>
              关闭
            </Button>
          ] : [
            <Button key="cancel" onClick={() => {
              setEditModalVisible(false);
              setEditingFile(null);
            }}>
              取消
            </Button>,
            <Button key="save" type="primary" loading={saving} onClick={handleSaveFile}>
              保存
            </Button>
          ]
        }
      >
        <div style={{ marginBottom: 12 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary">
              文件路径: {editingFile?.path || ''}
            </Text>
            {!editingFile?.name.toLowerCase().endsWith('.csv') && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                💡 提示: 支持语法高亮、代码补全、Ctrl+S保存、Ctrl+F查找
              </Text>
            )}
          </Space>
        </div>
        <div style={{ border: '1px solid #d9d9d9', borderRadius: 4, overflow: 'hidden' }}>
          {editingFile?.name.toLowerCase().endsWith('.csv') ? (
            <CsvViewer content={fileContent} />
          ) : (
            <CodeEditor
              value={fileContent}
              onChange={setFileContent}
              fileName={editingFile?.name}
              height="500px"
            />
          )}
        </div>
      </Modal>

      {/* 交互式终端弹窗 */}
      {terminalVisible && terminalScript && (
        <TerminalModal
          visible={terminalVisible}
          scriptPath={terminalScript.path}
          scriptName={terminalScript.name}
          onClose={() => {
            setTerminalVisible(false);
            setTerminalScript(null);
            addConsoleLog('='.repeat(60), 'info');
            addConsoleLog('交互式终端已关闭', 'info');
            addConsoleLog('='.repeat(60), 'info');
            loadFiles();
          }}
          onLog={(msg) => {
            // 将终端输出记录到控制台日志
            const lines = msg.split('\n');
            lines.forEach(line => {
              if (line.trim()) {
                addConsoleLog(line, 'info');
              }
            });
          }}
        />
      )}

      {/* Excel查看器 */}
      {excelViewerVisible && excelViewerFile && (
        <ExcelViewer
          visible={excelViewerVisible}
          filePath={excelViewerFile.path}
          fileName={excelViewerFile.name}
          onClose={() => {
            setExcelViewerVisible(false);
            setExcelViewerFile(null);
            addConsoleLog('Excel查看器已关闭', 'info');
          }}
        />
      )}

      {/* Word查看器 */}
      {wordViewerVisible && wordViewerFile && (
        <WordViewer
          visible={wordViewerVisible}
          filePath={wordViewerFile.path}
          fileName={wordViewerFile.name}
          onClose={() => {
            setWordViewerVisible(false);
            setWordViewerFile(null);
            addConsoleLog('Word查看器已关闭', 'info');
          }}
        />
      )}

      {/* PDF查看器 */}
      {pdfViewerVisible && pdfViewerFile && (
        <PdfViewer
          visible={pdfViewerVisible}
          filePath={pdfViewerFile.path}
          fileName={pdfViewerFile.name}
          onClose={() => {
            setPdfViewerVisible(false);
            setPdfViewerFile(null);
            addConsoleLog('PDF查看器已关闭', 'info');
          }}
        />
      )}
    </div>
  );
};

export default Workspace;
