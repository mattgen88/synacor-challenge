package main

import "fmt"
import "os"

func f6049(a int, b int, c int, cache map[string]int) int {
	key := fmt.Sprintf("%v|%v", a, b)
	if val, ok := cache[key]; ok {
		return val
	}
	var result int

	if a == 0 {
		result = (b + 1) % 32768
		cache[key] = result
		return result
	} else {
		if b == 0 {
			result = f6049(a-1, c, c, cache)
			cache[fmt.Sprintf("%v|%v", a-1, c)] = result
			return result
		} else {
			var tmp int
			tmp = f6049(a, b-1, c, cache)
			cache[fmt.Sprintf("%v|%v", a, b-1)] = tmp
			result = f6049(a-1, tmp, c, cache)
			cache[fmt.Sprintf("%v|%v", a, b)] = result
			cache[fmt.Sprintf("%v|%v", a-1, tmp)] = result
		}
	}
	return result
}

func calc(i int) <-chan bool {
	out := make(chan bool)
	go func() {
		var cache map[string]int
		cache = make(map[string]int)
		fmt.Println(fmt.Sprintf("Trying %v", i))
		var val int = f6049(4, 1, i, cache)
		fmt.Println(fmt.Sprintf("Value: %v", val))

		if val == 6 {
			out <- true
			fmt.Println("Found it")
			fmt.Sprintf("Value is %v", val)
		} else {
			out <- false
		}
		close(out)
	}()
	return out
}

func main() {
	for i := 1; i <= 32768; i++ {
		found := calc(i)
		if <-found {
			fmt.Println(fmt.Sprintf("Answer is %v", i))
			os.Exit(0)
		}
	}
	fmt.Println("Nothing found")
}
