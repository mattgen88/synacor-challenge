package main
import "fmt"
import "os"

var cache map[string]int

func dicks(a int, b int, c int) (int) {
  key := fmt.Sprintf("%v|%v", a, b)
  if val, ok := cache[key]; ok {
    return val
  }
  var result int

  if (a == 0) {
    result = (b + 1) % 32768
    cache[key] = result
    return result
  } else {
    if b == 0 {
      result = dicks(a - 1, c, c)
      cache[fmt.Sprintf("%v|%v", a -1, c)] = result
      return result
    } else {
      var tmp int
      tmp = dicks(a, b - 1, c)
      cache[fmt.Sprintf("%v|%v", a, b)] = tmp
      result = dicks(a - 1, tmp, c)
      cache[fmt.Sprintf("%v|%v", a, b)] = result
    }
  }
  return result
}

func main() {

  for i := 1; i <= 32768; i++ {
    cache = make(map[string]int)
    fmt.Println(fmt.Sprintf("Trying %v", i))
    var val int = dicks(4, 1, i)
    fmt.Println(fmt.Sprintf("Value: %v", val))
    if val == 6 {
      fmt.Println("Found it")
      fmt.Sprintf("Value is %v", val)
      os.Exit(0)
    }
  }
  fmt.Println("Nothing found");
}
