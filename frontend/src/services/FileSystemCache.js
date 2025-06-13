// 简化的缓存管理器
class SimpleCacheManager {
  constructor(maxSize = 100 * 1024 * 1024) {
    this.cache = new Map();
    this.maxSize = maxSize;
    this.currentSize = 0;
  }

  set(key, value, size = 0, ttl = 3600000) {
    // 如果缓存已满，清理最旧的条目
    if (this.currentSize + size > this.maxSize) {
      this.cleanup();
    }

    const item = {
      value,
      size,
      timestamp: Date.now(),
      ttl,
      accessCount: 0
    };

    this.cache.set(key, item);
    this.currentSize += size;
  }

  get(key) {
    const item = this.cache.get(key);
    if (!item) return null;

    // 检查是否过期
    if (Date.now() - item.timestamp > item.ttl) {
      this.delete(key);
      return null;
    }

    item.accessCount++;
    return item.value;
  }

  has(key) {
    return this.cache.has(key) && this.get(key) !== null;
  }

  delete(key) {
    const item = this.cache.get(key);
    if (item) {
      this.currentSize -= item.size;
      this.cache.delete(key);
    }
  }

  clear() {
    this.cache.clear();
    this.currentSize = 0;
  }

  cleanup() {
    const now = Date.now();
    let cleaned = 0;

    for (const [key, item] of this.cache.entries()) {
      if (now - item.timestamp > item.ttl) {
        this.delete(key);
        cleaned++;
      }
    }

    // 如果仍然超过限制，删除最少使用的条目
    if (this.currentSize > this.maxSize) {
      const entries = Array.from(this.cache.entries())
        .sort(([, a], [, b]) => a.accessCount - b.accessCount);

      for (const [key] of entries) {
        this.delete(key);
        cleaned++;
        if (this.currentSize <= this.maxSize * 0.8) break;
      }
    }

    return cleaned;
  }

  getStats() {
    return {
      size: this.cache.size,
      currentSize: this.currentSize,
      maxSize: this.maxSize
    };
  }
}

class FileSystemCache {
  constructor() {
    // 文件内容缓存 (100MB)
    this.fileCache = new SimpleCacheManager(100 * 1024 * 1024);
    // 目录结构缓存 (10MB)
    this.dirCache = new SimpleCacheManager(10 * 1024 * 1024);
    // 仓库元数据缓存 (5MB)
    this.repoCache = new SimpleCacheManager(5 * 1024 * 1024);
    
    // 定期清理过期缓存
    this.startCleanupInterval();
  }

  /**
   * 生成缓存键
   * @private
   */
  static generateKey(type, platform, repo, path = '') {
    return `${type}:${platform}:${repo}:${path}`;
  }

  /**
   * 计算数据大小
   * @private
   */
  static calculateSize(data) {
    return new TextEncoder().encode(JSON.stringify(data)).length;
  }

  /**
   * 缓存文件内容
   * @param {string} platform - 平台（github/gitlab）
   * @param {string} repo - 仓库名称
   * @param {string} path - 文件路径
   * @param {string} content - 文件内容
   * @param {number} ttl - 过期时间（毫秒）
   */
  async cacheFile(platform, repo, path, content, ttl = 3600000) {
    const key = FileSystemCache.generateKey('file', platform, repo, path);
    const size = FileSystemCache.calculateSize(content);
    this.fileCache.set(key, content, size, ttl);
  }

  /**
   * 获取缓存的文件内容
   * @param {string} platform - 平台
   * @param {string} repo - 仓库名称
   * @param {string} path - 文件路径
   * @returns {string|null} 文件内容
   */
  async getFile(platform, repo, path) {
    const key = FileSystemCache.generateKey('file', platform, repo, path);
    return this.fileCache.get(key);
  }

  /**
   * 缓存目录结构
   * @param {string} platform - 平台
   * @param {string} repo - 仓库名称
   * @param {string} path - 目录路径
   * @param {Array} structure - 目录结构
   * @param {number} ttl - 过期时间（毫秒）
   */
  cacheDirectory(platform, repo, path, structure, ttl = 1800000) {
    const key = FileSystemCache.generateKey('dir', platform, repo, path);
    const size = FileSystemCache.calculateSize(structure);
    this.dirCache.set(key, structure, size, ttl);
  }

  /**
   * 获取缓存的目录结构
   * @param {string} platform - 平台
   * @param {string} repo - 仓库名称
   * @param {string} path - 目录路径
   * @returns {Array|null} 目录结构
   */
  getDirectory(platform, repo, path) {
    const key = FileSystemCache.generateKey('dir', platform, repo, path);
    return this.dirCache.get(key);
  }

  /**
   * 缓存仓库元数据
   * @param {string} platform - 平台
   * @param {string} repo - 仓库名称
   * @param {Object} metadata - 仓库元数据
   * @param {number} ttl - 过期时间（毫秒）
   */
  cacheRepository(platform, repo, metadata, ttl = 7200000) {
    const key = FileSystemCache.generateKey('repo', platform, repo);
    const size = FileSystemCache.calculateSize(metadata);
    this.repoCache.set(key, metadata, size, ttl);
  }

  /**
   * 获取缓存的仓库元数据
   * @param {string} platform - 平台
   * @param {string} repo - 仓库名称
   * @returns {Object|null} 仓库元数据
   */
  getRepository(platform, repo) {
    const key = FileSystemCache.generateKey('repo', platform, repo);
    return this.repoCache.get(key);
  }

  /**
   * 清除指定仓库的所有缓存
   * @param {string} platform - 平台
   * @param {string} repo - 仓库名称
   */
  clearRepositoryCache(platform, repo) {
    const prefix = `${platform}:${repo}:`;
    
    [this.fileCache, this.dirCache, this.repoCache].forEach(cache => {
      for (const [key] of cache.cache.entries()) {
        if (key.includes(prefix)) {
          cache.delete(key);
        }
      }
    });
  }

  /**
   * 清除所有缓存
   */
  clearAll() {
    this.fileCache.clear();
    this.dirCache.clear();
    this.repoCache.clear();
  }

  /**
   * 获取缓存状态
   * @returns {Object} 缓存统计信息
   */
  getStatus() {
    return {
      files: this.fileCache.getStats(),
      directories: this.dirCache.getStats(),
      repositories: this.repoCache.getStats()
    };
  }

  /**
   * 启动定期清理
   * @private
   */
  startCleanupInterval() {
    // 每5分钟清理一次过期缓存
    this.cleanupInterval = setInterval(() => {
      this.fileCache.cleanup();
      this.dirCache.cleanup();
      this.repoCache.cleanup();
    }, 300000);
  }

  /**
   * 停止定期清理
   */
  stopCleanupInterval() {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }
  }

}

// 导出类和单例实例
export { FileSystemCache };
const fileSystemCache = new FileSystemCache();
export default fileSystemCache;
