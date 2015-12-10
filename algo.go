package main

import "fmt"
import "os"

var cache [32768 * 8]uint32

func f6049(a uint32, b uint32, c uint32) uint32 {
	key := (a * 32768) + b
	if cache[key] > 0 {
		return cache[key]
	}
	var result uint32

	if a == 0 {
		result = (b + 1) % 32768
	} else {
		if b == 0 {
			result = f6049(a-1, c, c)
			return result
		} else {
			var tmp uint32
			tmp = f6049(a, b-1, c)
			result = f6049(a-1, tmp, c)

		}
	}
	cache[key] = result
	return result
}

func calc(i uint32) <-chan bool {
	out := make(chan bool)
	go func() {
		cache = [32768 * 8]uint32{0}
		//fmt.Println(fmt.Sprintf("Trying %v", i))
		var val uint32 = f6049(4, 1, i)
		//fmt.Println(fmt.Sprintf("Value: %v", val))

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
	var i uint32
	for i = 1; i <= 32768; i++ {
		if i%100 == 0 {
			fmt.Println(fmt.Sprintf("Trying block %v", i))
		}
		found := calc(i)
		if <-found {
			fmt.Println(fmt.Sprintf("Answer is %v", i))
			os.Exit(0)
		}
	}
	fmt.Println("Nothing found")
}
