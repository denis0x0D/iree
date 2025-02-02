// RUN: iree-tf-opt -split-input-file -verify-diagnostics -iree-guarantee-all-funcs-one-use <%s | IreeFileCheck %s

// -----
// Basic test.
// CHECK-LABEL: func @f
func @f() {
  // CHECK: call @g() : () -> ()
  // CHECK: call @[[NEWG:.+]]() : () -> ()
  call @g() : () -> ()
  call @g() : () -> ()
  return
}

// CHECK: func @g()
// CHECK: func @[[NEWG]]() attributes {sym_visibility = "private"}
func @g() {
  return
}

// -----
// Transitive callees.
// CHECK-LABEL: func @f
// 2 copies of @g
// CHECK-DAG: func @g{{.*}}
// CHECK-DAG: func @g{{.*}}
// 4 copies of @h
// CHECK-DAG: func @h{{.*}}
// CHECK-DAG: func @h{{.*}}
// CHECK-DAG: func @h{{.*}}
// CHECK-DAG: func @h{{.*}}
func @f() {
  call @g() : () -> ()
  call @g() : () -> ()
  return
}

func @g() {
  call @h() : () -> ()
  call @h() : () -> ()
  return
}

func @h() {
  return
}

// -----
// Handle error case of infinite recursion.
// expected-error @+1 {{reached cloning limit}}
func @f() attributes {sym_visibility = "private"} {
  call @f() : () -> ()
  call @f() : () -> ()
  return
}
