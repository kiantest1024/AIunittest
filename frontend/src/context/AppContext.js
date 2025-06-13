import { createContext, useReducer, useContext } from 'react';

// 初始状态
const initialState = {
  code: '',
  language: 'java',
  model: 'deepseek-V3',
  generatedTests: [],
  loading: false,
  error: null
};

// 创建上下文
const AppContext = createContext();

// 定义操作类型
const ActionTypes = {
  SET_CODE: 'SET_CODE',
  SET_LANGUAGE: 'SET_LANGUAGE',
  SET_MODEL: 'SET_MODEL',
  SET_GENERATED_TESTS: 'SET_GENERATED_TESTS',
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  RESET: 'RESET'
};

// Reducer
function appReducer(state, action) {
  switch (action.type) {
    case ActionTypes.SET_CODE:
      return { ...state, code: action.payload };
    case ActionTypes.SET_LANGUAGE:
      return { ...state, language: action.payload, generatedTests: [] };
    case ActionTypes.SET_MODEL:
      return { ...state, model: action.payload };
    case ActionTypes.SET_GENERATED_TESTS:
      console.log('Is array:', Array.isArray(action.payload));
      // 确保 payload 是数组
      let tests = [];
      if (Array.isArray(action.payload)) {
        tests = [...action.payload]; // 创建一个新数组
      } else if (action.payload && typeof action.payload === 'object') {
        // 尝试从对象中提取测试
        if (action.payload.tests && Array.isArray(action.payload.tests)) {
          tests = [...action.payload.tests];
        }
      }

      return { ...state, generatedTests: tests };
    case ActionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
    case ActionTypes.SET_ERROR:
      return { ...state, error: action.payload };
    case ActionTypes.RESET:
      return initialState;
    default:
      return state;
  }
}

// Provider组件
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// 自定义Hook
export function useAppContext() {
  return useContext(AppContext);
}

// 导出操作类型
export { ActionTypes };
