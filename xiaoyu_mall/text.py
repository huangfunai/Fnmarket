# day 1
# 926. 将字符串翻转到单调递增    https://leetcode.cn/problems/flip-string-to-monotone-increasing/

# 动态规划
'''
s = "00110"

dp0, dp1 = 0, 0
for c in s:
	ndp0, ndp1 = dp0, min(dp0, dp1)
	if c == '1':
		ndp0 += 1
	else:
		ndp1 += 1
	dp0, dp1 = ndp0, ndp1
	print(ndp0, ndp1)
	print(min(dp0, dp1))
'''

# day 2 https://leetcode.cn/problems/find-and-replace-pattern/
# 查找和替换模式

# 双映射哈希表
'''
words = ["abc","deq","mee","aqq","dkd","ccc"]
pattern = "abb"

def match(word: str, pattern: str) -> bool:
	mp = {}
	for x, y in zip(word, pattern):
		if x not in mp:
			mp[x] = y
		elif mp[x] != y:    # word 中的同一个字母必须要映射到 pattern 中的同一个字母上
			return False
	return True
print([word for word in words if match(word, pattern) and match(pattern, word)])
'''

# day 3 https://leetcode.cn/problems/height-checker/
#  高度检查器

# 比较 排序
heights = [1,1,4,2,1,3]

count = 0
for i in range(len(heights)):
	if heights[i] != sorted(heights)[i]:
		count += 1
print(count)

