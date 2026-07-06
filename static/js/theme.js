/* ============================================================
   نظام إدارة الثيم (Dark/Light Mode)
   ============================================================ */

class ThemeManager {
  constructor() {
    this.STORAGE_KEY = 'app-theme';
    this.THEME_ATTRIBUTE = 'data-theme';
    this.LIGHT_MODE = 'light';
    this.DARK_MODE = 'dark';
    
    // تهيئة الثيم عند تحميل الصفحة
    this.init();
  }

  /**
   * تهيئة نظام الثيم
   */
  init() {
    const savedTheme = this.getSavedTheme();
    const preferredTheme = this.getSystemPreference();
    const initialTheme = savedTheme || preferredTheme || this.LIGHT_MODE;
    
    this.setTheme(initialTheme);
    this.setupToggleButton();
    this.setupSystemThemeListener();
  }

  /**
   * الحصول على الثيم المحفوظ من localStorage
   */
  getSavedTheme() {
    return localStorage.getItem(this.STORAGE_KEY);
  }

  /**
   * الحصول على تفضيل نظام التشغيل
   */
  getSystemPreference() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return this.DARK_MODE;
    }
    return this.LIGHT_MODE;
  }

  /**
   * تعيين الثيم الحالي
   */
  setTheme(theme) {
    // التحقق من أن الثيم صحيح
    if (theme !== this.LIGHT_MODE && theme !== this.DARK_MODE) {
      theme = this.LIGHT_MODE;
    }

    // تطبيق الثيم على الـ DOM
    document.documentElement.setAttribute(this.THEME_ATTRIBUTE, theme);

    // حفظ الاختيار في localStorage
    localStorage.setItem(this.STORAGE_KEY, theme);

    // تحديث زر التبديل
    this.updateToggleButton(theme);

    // إطلاق حدث مخصص
    this.dispatchThemeChangeEvent(theme);
  }

  /**
   * تبديل بين الثيمات
   */
  toggleTheme() {
    const currentTheme = document.documentElement.getAttribute(this.THEME_ATTRIBUTE) || this.LIGHT_MODE;
    const newTheme = currentTheme === this.LIGHT_MODE ? this.DARK_MODE : this.LIGHT_MODE;
    this.setTheme(newTheme);
  }

  /**
   * إعداد زر تبديل الثيم
   */
  setupToggleButton() {
    const toggleButton = document.getElementById('theme-toggle-btn');
    if (!toggleButton) return;

    toggleButton.addEventListener('click', () => {
      this.toggleTheme();
    });

    // تحديث الزر بناءً على الثيم الحالي
    const currentTheme = document.documentElement.getAttribute(this.THEME_ATTRIBUTE) || this.LIGHT_MODE;
    this.updateToggleButton(currentTheme);
  }

  /**
   * تحديث نص/أيقونة زر التبديل
   */
  updateToggleButton(theme) {
    const toggleButton = document.getElementById('theme-toggle-btn');
    if (!toggleButton) return;

    if (theme === this.DARK_MODE) {
      toggleButton.innerHTML = '☀️ وضع فاتح';
      toggleButton.setAttribute('aria-label', 'تبديل إلى الوضع الفاتح');
    } else {
      toggleButton.innerHTML = '🌙 وضع مظلم';
      toggleButton.setAttribute('aria-label', 'تبديل إلى الوضع المظلم');
    }
  }

  /**
   * الاستماع لتغييرات نظام التشغيل
   */
  setupSystemThemeListener() {
    if (!window.matchMedia) return;

    const darkModeMediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // للمتصفحات الحديثة
    if (darkModeMediaQuery.addEventListener) {
      darkModeMediaQuery.addEventListener('change', (e) => {
        // تطبيق التغيير فقط إذا لم يكن هناك اختيار يدوي من المستخدم
        if (!this.getSavedTheme()) {
          const newTheme = e.matches ? this.DARK_MODE : this.LIGHT_MODE;
          this.setTheme(newTheme);
        }
      });
    }
  }

  /**
   * إطلاق حدث مخصص عند تغيير الثيم
   */
  dispatchThemeChangeEvent(theme) {
    const event = new CustomEvent('themechange', {
      detail: { theme: theme }
    });
    document.dispatchEvent(event);
  }

  /**
   * الحصول على الثيم الحالي
   */
  getCurrentTheme() {
    return document.documentElement.getAttribute(this.THEME_ATTRIBUTE) || this.LIGHT_MODE;
  }

  /**
   * التحقق من وضع مظلم نشط
   */
  isDarkMode() {
    return this.getCurrentTheme() === this.DARK_MODE;
  }

  /**
   * التحقق من وضع فاتح نشط
   */
  isLightMode() {
    return this.getCurrentTheme() === this.LIGHT_MODE;
  }
}

// تهيئة نظام الثيم عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
  window.themeManager = new ThemeManager();
});

// يمكن استخدام الحدث المخصص في أي مكان في التطبيق
document.addEventListener('themechange', function(e) {
  console.log('تم تغيير الثيم إلى:', e.detail.theme);
  // يمكنك إضافة منطق إضافي هنا
});
