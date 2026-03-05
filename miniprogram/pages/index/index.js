// pages/index/index.js
const API_URL = 'http://localhost:8000/news'; // 本地开发地址

Page({
  data: {
    newsList: [],
    loading: true
  },

  onLoad() {
    this.fetchNews();
  },

  onPullDownRefresh() {
    this.fetchNews(() => {
      wx.stopPullDownRefresh();
    });
  },

  fetchNews(cb) {
    const that = this;
    wx.request({
      url: API_URL,
      method: 'GET',
      success(res) {
        if (res.statusCode === 200) {
          // 处理数据，添加 expanded 状态
          const list = res.data.map(item => {
            // 简单的 markdown 转 HTML (演示用，实际建议用 parser)
            // 这里假设 summary 已经是处理好的文本，或者包含简单的换行
            let summaryHtml = item.summary.replace(/\n/g, '<br/>');
            // 处理图片 markdown ![alt](url) -> <img src="url"/>
            summaryHtml = summaryHtml.replace(/!\[.*?\]\((.*?)\)/g, '<img src="$1" style="width:100%;"/>');
            
            return {
              ...item,
              expanded: false,
              summary_html: summaryHtml
            };
          });
          
          that.setData({
            newsList: list,
            loading: false
          });
        }
      },
      fail(err) {
        console.error('请求失败', err);
        wx.showToast({
          title: '网络错误',
          icon: 'none'
        });
        that.setData({ loading: false });
      },
      complete() {
        if (cb) cb();
      }
    });
  },

  toggleSummary(e) {
    const index = e.currentTarget.dataset.index;
    const key = `newsList[${index}].expanded`;
    const currentVal = this.data.newsList[index].expanded;
    
    this.setData({
      [key]: !currentVal
    });
  }
})
