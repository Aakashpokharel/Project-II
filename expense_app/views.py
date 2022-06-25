from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from .models import Expense, ExpenseCategory
from django.contrib import messages
from django.utils.timezone import localtime
from user_profile.models import UserProfile
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.db.models import Sum
import xlwt
from .utils import queryset_filter
import pandas as pd
import datetime
from .utils import expense_send_success_mail,expense_send_error_mail
from pyexcel_xls import get_data as xls_get
from pyexcel_xlsx import get_data as xlsx_get
from datetime import datetime as datetime_custom
from django.db.models import Q

@login_required(login_url='login')
def expense_page(request):

    filter_context = {}
    base_url = f''
    date_from_html = ''
    date_to_html = ''

    expenses =  Expense.objects.filter(
        user = request.user
    ).order_by('-date')

    try:

        if 'date_from' in request.GET and request.GET['date_from'] != '':
            date_from = datetime_custom.strptime(request.GET['date_from'],'%Y-%m-%d')
            filter_context['date_from'] = request.GET['date_from']
            date_from_html = request.GET['date_from']

            if 'date_to' in request.GET and request.GET['date_to'] != '':

                date_to = datetime_custom.strptime(request.GET['date_to'],'%Y-%m-%d')
                filter_context['date_to'] = request.GET['date_to']
                date_to_html = request.GET['date_to']
                expenses = expenses.filter(
                    Q(date__gte = date_from )
                    &
                    Q(date__lte = date_to)
                ).order_by('-date')

            else:
                expenses = expenses.filter(
                    date__gte = date_from
                ).order_by('-date')

        elif 'date_to' in request.GET and request.GET['date_to'] != '':

            date_to_html = request.GET['date_to']
            date_to = datetime_custom.strptime(request.GET['date_to'],'%Y-%m-%d')
            filter_context['date_from'] = request.GET['date_to']
            expenses = expenses.filter(
                date__lte = date_to
            ).order_by('-date')
    
    except:
        messages.error(request,'Something went wrong')
        return redirect('expense')
    
    base_url = f'?date_from={date_from_html}&date_to={date_to_html}&'
    paginator = Paginator(expenses,5)
    page_number = request.GET.get('page')
    page_expenses = Paginator.get_page(paginator,page_number)

    if UserProfile.objects.filter(user = request.user).exists():
        currency = UserProfile.objects.get(user = request.user).currency
    else:
        currency = 'NPR - Neplease Rupees'

    return render(request,'expense_app/expense.html',{
        'currency':currency,
        'page_expenses':page_expenses,
        'expenses':expenses,
        'filter_context':filter_context,
        'base_url':base_url
    })

@login_required(login_url='login')
def add_expense(request):
    
    if ExpenseCategory.objects.filter(user=request.user).exists():
        
        categories = ExpenseCategory.objects.filter(user=request.user)

        context = {
            'categories' : categories,
            'values':request.POST
        }

        if request.method == 'GET':
            return render(request,'expense_app/add_expense.html',context)

        if request.method == 'POST':
            amount = request.POST.get('amount','')
            description = request.POST.get('description','')
            category = request.POST.get('category','')
            date = request.POST.get('expense_date','')

            if amount== '':
                messages.error(request,'Amount cannot be empty')
                return render(request,'expense_app/add_expense.html',context)
            
            amount = float(amount)
            if amount <= 0:
                messages.error(request,'Amount should be greater than zero')
                return render(request,'expense_app/add_expense.html',context)

            if description == '':
                messages.error(request,'Description cannot be empty')
                return render(request,'expense_app/add_expense.html',context)

            if category == '':
                messages.error(request,'ExpenseCategory cannot be empty')
                return render(request,'expense_app/add_expense.html',context)

            if date == '':
                date = localtime()

            category_obj = ExpenseCategory.objects.get(user=request.user,name =category)
            Expense.objects.create(
                user=request.user,
                amount=amount,
                date=date,
                description=description,
                category=category_obj
            ).save()

            messages.success(request,'Expense Saved Successfully')
            return redirect('expense')
    else:
        messages.error(request,'Please add a category first.')
        return redirect('add_expense_category')

@login_required(login_url='login')
def add_expense_category(request):
    
    categories = ExpenseCategory.objects.filter(user=request.user)

    context = {
        'categories' : categories,
        'values':request.POST,
        'create':True
    }

    if request.method == 'GET': 
        return render(request,'expense_app/expense_category_import.html',context)

    if request.method == 'POST':
        name = request.POST.get('name','')

        if name == '':
            messages.error(request,'Expense Category cannot be empty')
            return render(request,'expense_app/expense_category_import.html',context)
        
        name = name.lower().capitalize()
        if ExpenseCategory.objects.filter(user=request.user,name = name).exists():
            messages.error(request,f'Expense Category ({name}) already exists.')
            return render(request,'expense_app/expense_category_import.html',context)
        
        ExpenseCategory.objects.create(user=request.user,name = name).save()

        messages.success(request,'Expense Category added')
        return render(request,'expense_app/expense_category_import.html',{
            'categories' : categories,
            'create':True
        })

@login_required(login_url='login')
def edit_expense_category(request,id):

    if ExpenseCategory.objects.filter(user=request.user,pk=id).exists():
        category = ExpenseCategory.objects.get(user=request.user,pk=id)
    else:
        messages.error(request,'Something Went Wrong')
        return redirect('add_expense_category')

    if category.user != request.user:
        messages.error(request,'Something Went Wrong')
        return redirect('add_expense_category')

    context = {
        'value':category.name,
        'update':True,
        'id':category.id
    }

    if request.method == 'GET': 
        return render(request,'expense_app/expense_category_import.html',context)

    if request.method == 'POST':
        name = request.POST.get('name','')

        context = {
            'value':name,
            'update':True,
            'id':category.id
        }

        if name == '':
            messages.error(request,'Expense Category cannot be empty')
            return render(request,'expense_app/expense_category_import.html',context)
        
        name = name.lower().capitalize()
        if ExpenseCategory.objects.filter(user=request.user,name = name).exists():
            messages.error(request,f'Expense Category ({name}) already exists.')
            return render(request,'expense_app/expense_category_import.html',context)
        
        category.name = name
        category.save()

        messages.success(request,'Expense Category Updated')
        return redirect('add_expense_category')

@login_required(login_url='login')
def delete_expense_category(request,id):

    if ExpenseCategory.objects.filter(id=id,user=request.user).exists():
        category = ExpenseCategory.objects.get(id=id,user=request.user)
        
        if category.user != request.user:
            messages.error(request,'You cannot delete this catgeory.')
            return redirect('add_expense_category')
        
        else:
            category.delete()
            messages.success(request,'Deleted category')
            return redirect('add_expense_category')
    
    messages.error(request,'Please try again')
    return redirect('add_expense_category')

@login_required(login_url='login')
def edit_expense(request,id):
    
    if Expense.objects.filter(id=id,user=request.user).exists():
        expense = Expense.objects.get(id=id,user=request.user)
    
    else:
        messages.error(request,'Something went Wrong. Please Try Again')
        return redirect('expense')
    
    if expense.user != request.user:
        messages.error(request,'Something Went Wrong')
        return redirect('expense')
    
    categories = ExpenseCategory.objects.filter(user=request.user).exclude(id=expense.category.id)

    context = {
        'expense':expense,
        'values': expense,
        'categories':categories
    }
    
    if request.method == 'GET':
        return render(request,'expense_app/edit_expense.html',context)

    if request.method == 'POST':
        amount = request.POST.get('amount','')
        description = request.POST.get('description','')
        category = request.POST.get('category','')
        date = request.POST.get('expense_date','')
        
        if amount== '':
            messages.error(request,'Amount cannot be empty')
            return render(request,'expense_app/edit_expense.html',context)
        
        amount = float(amount)
        if amount <= 0:
            messages.error(request,'Amount should be greater than zero')
            return render(request,'expense_app/edit_expense.html',context)
        
        if description == '':
            messages.error(request,'Description cannot be empty')
            return render(request,'expense_app/edit_expense.html',context)
        
        if category == '':
            messages.error(request,'ExpenseCategory cannot be empty')
            return render(request,'expense_app/edit_expense.html',context)
        
        if date == '':
            date = localtime()
        
        category_obj = ExpenseCategory.objects.get(user=request.user,name =category)
        expense.amount = amount
        expense.date = date
        expense.category = category_obj
        expense.description = description
        expense.save() 
        
        messages.success(request,'Expense Updated Successfully')
        return redirect('expense')

@login_required(login_url='login')
def delete_expense(request,id):
    
    if Expense.objects.filter(id=id,user=request.user).exists():
        expense = Expense.objects.get(id=id,user=request.user)
        
        if expense.user != request.user:
            messages.error(request,'Something Went Wrong')
            return redirect('expense')
        
        else:
            expense.delete()
            messages.success(request,'Expense Deleted Successfully')
            return redirect('expense')
    else:
        messages.error(request,'Something went Wrong. Please Try Again')
        return redirect('expense')

@login_required(login_url='login')
def download_as_excel(request,filter_by):
    filter_by = str(filter_by)
    response = HttpResponse(content_type = 'application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Expenses-'+ str(request.user.username) + '-' + str(localtime())+".xls"
    
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Expenses')
    
    if filter_by != '':
        ws.write(0,0,f"Expenses in {filter_by.lower().capitalize()}")
    else:
        ws.write(0,0,f"Expenses in Year")
    
    row_number = 1
    fontStyle = xlwt.XFStyle()
    fontStyle.font.bold = True
    columns = ['Date','Category','Description','Amount']
    
    for col_num in range(len(columns)):
        ws.write(row_number,col_num,columns[col_num],fontStyle)
    fontStyle = xlwt.XFStyle()

    expenses = queryset_filter(User.objects.get(username=request.user.username),filter_by).order_by('date')
    rows = expenses.values_list('date','category__name','description','amount')
    for row in rows:
        row_number += 1
        for col_num in range(len(row)):
            ws.write(row_number,col_num,str(row[col_num]),fontStyle)
    
    row_number +=2
    style = xlwt.easyxf('font: colour red, bold True;')
    ws.write(row_number,0,'TOTAL',style)
    ws.write(row_number,3,str(expenses.aggregate(Sum('amount'))['amount__sum']),style)
    wb.save(response)
    return response

@login_required(login_url='login')
def expense_page_sort(request):

    expenses =  Expense.objects.filter(user=request.user)
    base_url = ''

    try:
    
        if 'amount_sort' in request.GET and request.GET.get('amount_sort'):
            base_url = f'?amount_sort={request.GET.get("amount_sort",2)}&'
            if int(request.GET.get('amount_sort',2)) == 1:
                expenses = expenses.order_by('-amount')
            elif int(request.GET.get('amount_sort',2)) == 2:
                expenses = expenses.order_by('amount')
        
        if 'date_sort' in request.GET and request.GET.get('date_sort'):
            base_url = f'?date_sort={request.GET.get("date_sort",2)}&'
            if int(request.GET.get('date_sort',2)) == 1:
                expenses = expenses.order_by('-date')
            elif int(request.GET.get('date_sort',2)) == 2:
                expenses = expenses.order_by('date')
    
    except:
        messages.error(request,'Something went wrong')
        return redirect('expense')

    paginator = Paginator(expenses,5)
    page_number = request.GET.get('page')
    page_expenses = Paginator.get_page(paginator,page_number)

    if UserProfile.objects.filter(user = request.user).exists():
        currency = UserProfile.objects.get(user = request.user).currency
    else:
        currency = 'NPR - Neplease Rupees'

    return render(request,'expense_app/expense.html',{
        'currency':currency,
        'page_expenses':page_expenses,
        'expenses':expenses,
        'base_url':base_url
    })